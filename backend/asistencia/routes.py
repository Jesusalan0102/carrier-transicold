# backend/asistencia/routes.py
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timezone, timedelta
import json, os, uuid, hashlib, base64, math, time

# Tijuana = UTC-7 (no observa horario de verano desde 2022 en Baja California)
TIJUANA_TZ = timezone(timedelta(hours=-7))

from auth import verify_token

router = APIRouter()

# ==================== MODELOS ====================
class RegistroAsistencia(BaseModel):
    token: str
    lat_tecnico: float
    lon_tecnico: float
    selfie_base64: str
    gps_accuracy: Optional[float] = None

class ConfiguracionAsistencia(BaseModel):
    lat_fija: float
    lon_fija: float
    radio_metros: int
    tiempo_expiracion: int = 300


# ==================== CONFIGURACIÓN PERSISTENTE ====================
CONFIG_PATH = "storage/asistencia_config.json"
os.makedirs("storage/selfies", exist_ok=True)

_config = {
    "lat_fija": 32.5027,
    "lon_fija": -117.0037,
    "radio_metros": 200,
    "tiempo_expiracion": 300
}

if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH) as f:
            _config = json.load(f)
    except Exception:
        pass


# ==================== TOKEN CORTO ====================
# El token solo contiene: expiracion + firma(lat,lon,radio,exp)
# La config real se lee del servidor → URL mucho más corta

SECRET = "carrier_qr_2024"  # clave interna para firmar QR

def _firma(lat: float, lon: float, radio: int, exp: int) -> str:
    data = f"{lat}:{lon}:{radio}:{exp}:{SECRET}"
    return hashlib.sha256(data.encode()).hexdigest()[:12]

def generar_token_corto() -> str:
    exp = int(time.time()) + _config["tiempo_expiracion"]
    sig = _firma(_config["lat_fija"], _config["lon_fija"], _config["radio_metros"], exp)
    payload = f"{exp}:{sig}"
    return base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")

def validar_token_corto(token: str):
    try:
        # Agregar padding si falta
        padding = 4 - len(token) % 4
        if padding != 4:
            token += "=" * padding
        decoded = base64.urlsafe_b64decode(token).decode()
        exp_str, sig_recibida = decoded.rsplit(":", 1)
        exp = int(exp_str)
        if exp < int(time.time()):
            return False, "QR expirado"
        sig_esperada = _firma(_config["lat_fija"], _config["lon_fija"], _config["radio_metros"], exp)
        if sig_recibida != sig_esperada:
            return False, "QR inválido"
        return True, "OK"
    except Exception:
        return False, "QR inválido"


# ==================== UTILIDADES ====================
def calcular_distancia(lat1, lon1, lat2, lon2) -> float:
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def guardar_selfie(b64: str, username: str, fecha: str):
    try:
        data = b64.split(",")[1] if "," in b64 else b64
        img = base64.b64decode(data)
        if len(img) < 1000:
            return None
        fn = f"{username}_{fecha}_{uuid.uuid4().hex[:8]}.jpg"
        path = os.path.join("storage/selfies", fn)
        with open(path, "wb") as f:
            f.write(img)
        return f"storage/selfies/{fn}"
    except Exception:
        return None


# ==================== ENDPOINTS ====================

@router.get("/api/asistencia/configuracion")
async def get_configuracion(current_user=Depends(verify_token)):
    return _config

@router.post("/api/asistencia/configuracion")
async def set_configuracion(config: ConfiguracionAsistencia, current_user=Depends(verify_token)):
    global _config
    _config = config.dict()
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(_config, f)
    except Exception:
        pass
    return {"mensaje": "Configuración guardada", "config": _config}

@router.get("/api/asistencia/generar-qr")
async def generar_qr(request: Request, current_user=Depends(verify_token)):
    token = generar_token_corto()
    # Detectar HTTPS real (detrás de proxy en cleverapps/render)
    proto = request.headers.get("x-forwarded-proto", "")
    base = str(request.base_url).rstrip("/")
    if proto == "https":
        base = "https://" + base.split("://", 1)[-1]
    qr_url = f"{base}/app/checkin?t={token}"
    return {
        "qr_url": qr_url,
        "config": _config,
        "expiracion_segundos": _config["tiempo_expiracion"],
        "url_length": len(qr_url)   # para debug
    }

@router.post("/api/asistencia/registrar")
async def registrar_asistencia(registro: RegistroAsistencia, request: Request):
    from db import execute_write, execute_read

    # ── JWT ──────────────────────────────────────────────────────────────
    auth = request.headers.get("Authorization", "")
    username = None
    if auth.startswith("Bearer "):
        try:
            from jose import jwt as _jwt
            payload_jwt = _jwt.decode(auth[7:],
                os.getenv("SECRET_KEY", "carrier_secret_key_2024_change_in_production"),
                algorithms=["HS256"])
            username = payload_jwt.get("sub")
        except Exception:
            pass
    if not username:
        raise HTTPException(status_code=401, detail="Token JWT inválido")

    # ── Validar QR (soporta token largo legacy Y token corto nuevo) ──────
    valido, msg = validar_token_corto(registro.token)
    if not valido:
        raise HTTPException(status_code=400, detail=msg)

    lat_fija  = _config["lat_fija"]
    lon_fija  = _config["lon_fija"]
    radio     = _config["radio_metros"]

    # ── Distancia ─────────────────────────────────────────────────────────
    dist = calcular_distancia(registro.lat_tecnico, registro.lon_tecnico, lat_fija, lon_fija)
    if dist > radio:
        raise HTTPException(status_code=400,
            detail=f"Fuera del área ({dist:.0f}m, radio {radio}m)")

    # ── GPS accuracy ──────────────────────────────────────────────────────
    if registro.gps_accuracy and registro.gps_accuracy > 100:
        raise HTTPException(status_code=400,
            detail=f"Señal GPS débil ({registro.gps_accuracy:.0f}m). Espera al aire libre.")

    # ── Doble registro ────────────────────────────────────────────────────
    ahora_tj = datetime.now(TIJUANA_TZ)
    hoy = ahora_tj.strftime("%Y-%m-%d")
    if execute_read("SELECT id FROM asistencia WHERE username=%s AND fecha=%s", (username, hoy)):
        raise HTTPException(status_code=400, detail="Ya registraste asistencia hoy")

    # ── Selfie ────────────────────────────────────────────────────────────
    ruta = guardar_selfie(registro.selfie_base64, username, datetime.now().strftime("%Y%m%d"))

    # ── DB ────────────────────────────────────────────────────────────────
    hora = ahora_tj.strftime("%H:%M")
    try:
        execute_write("""
            INSERT INTO asistencia
              (username, fecha, hora, lat_fija, lon_fija, radio,
               lat_tecnico, lon_tecnico, distancia_m, dentro_radio)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (username, hoy, hora, lat_fija, lon_fija, radio,
              registro.lat_tecnico, registro.lon_tecnico, int(round(dist)),
              1 if dist <= radio else 0))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error DB: {e}")

    return {"exito": True, "mensaje": f"✅ Asistencia registrada. Distancia: {dist:.0f}m", "hora": hora}

@router.get("/api/asistencia/registros")
async def obtener_registros(fecha: Optional[str] = None, current_user=Depends(verify_token)):
    from db import execute_read
    query = """
        SELECT id, username, fecha, hora AS hora_checkin,
               lat_fija, lon_fija, radio AS radio_metros,
               lat_tecnico, lon_tecnico, distancia_m AS distancia_metros,
               dentro_radio AS aprobado, created_at
        FROM asistencia
        WHERE fecha=%s
        ORDER BY hora DESC
    """
    hoy2 = fecha if fecha else datetime.now().strftime("%Y-%m-%d")
    rows = execute_read(query, (hoy2,))
    return rows or []
