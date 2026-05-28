# backend/asistencia/routes.py
from fastapi import APIRouter, HTTPException, Request, Depends
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import json
import os
import uuid
import hashlib
import base64
import math

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


# ==================== CONFIGURACIÓN GLOBAL ====================
# Se persiste en archivo JSON para sobrevivir reinicios del servidor
CONFIG_PATH = "storage/asistencia_config.json"
os.makedirs("storage", exist_ok=True)
BASE_SELFIES_DIR = "storage/selfies"
os.makedirs(BASE_SELFIES_DIR, exist_ok=True)

_configuracion_asistencia = {
    "lat_fija": 32.5027,
    "lon_fija": -117.0037,
    "radio_metros": 200,
    "tiempo_expiracion": 300
}

# Cargar configuración guardada si existe
if os.path.exists(CONFIG_PATH):
    try:
        with open(CONFIG_PATH, "r") as f:
            _configuracion_asistencia = json.load(f)
    except Exception:
        pass


# ==================== FUNCIONES AUXILIARES ====================
def calcular_distancia(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def generar_token_seguro(lat: float, lon: float, radio: int) -> str:
    timestamp = int(datetime.now().timestamp())
    exp = timestamp + _configuracion_asistencia["tiempo_expiracion"]
    data_str = f"{lat}:{lon}:{radio}:{exp}"
    signature = hashlib.sha256(data_str.encode()).hexdigest()[:16]
    payload = {"lat": lat, "lon": lon, "radio": radio, "exp": exp, "sig": signature}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def validar_token(token: str):
    try:
        # Soportar tanto urlsafe como standard base64
        try:
            decoded = base64.urlsafe_b64decode(token + "==").decode()
        except Exception:
            decoded = base64.b64decode(token + "==").decode()
        payload = json.loads(decoded)
        if payload.get("exp", 0) < datetime.now().timestamp():
            return False, None, "QR expirado"
        expected_sig = hashlib.sha256(
            f"{payload['lat']}:{payload['lon']}:{payload['radio']}:{payload['exp']}".encode()
        ).hexdigest()[:16]
        if payload.get("sig") != expected_sig:
            return False, None, "QR inválido"
        return True, payload, "OK"
    except Exception:
        return False, None, "QR inválido"


def decode_base64_image(base64_string: str) -> bytes:
    if "," in base64_string:
        base64_string = base64_string.split(",")[1]
    return base64.b64decode(base64_string)


def guardar_selfie_sync(base64_image: str, username: str, fecha: str):
    """Guarda selfie de forma síncrona (sin aiofiles)"""
    try:
        image_bytes = decode_base64_image(base64_image)
        if not image_bytes or len(image_bytes) < 1000:
            return False, None, "Imagen inválida o muy pequeña"
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{username}_{fecha}_{unique_id}.jpg"
        filepath = os.path.join(BASE_SELFIES_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(image_bytes)
        return True, f"storage/selfies/{filename}", "OK"
    except Exception as e:
        return False, None, str(e)


# ==================== ENDPOINTS ====================

@router.get("/api/asistencia/configuracion")
async def get_configuracion(current_user=Depends(verify_token)):
    """Obtiene la configuración actual de asistencia"""
    return _configuracion_asistencia


@router.post("/api/asistencia/configuracion")
async def set_configuracion(config: ConfiguracionAsistencia, current_user=Depends(verify_token)):
    """Actualiza la configuración de asistencia y la persiste en disco"""
    global _configuracion_asistencia
    _configuracion_asistencia = config.dict()
    # Persistir en disco para sobrevivir reinicios
    try:
        with open(CONFIG_PATH, "w") as f:
            json.dump(_configuracion_asistencia, f)
    except Exception:
        pass
    return {"mensaje": "Configuración actualizada", "config": _configuracion_asistencia}


@router.get("/api/asistencia/generar-qr")
async def generar_qr(request: Request, current_user=Depends(verify_token)):
    """Genera el token QR de asistencia con la configuración actual"""
    config = _configuracion_asistencia
    token = generar_token_seguro(
        config["lat_fija"], config["lon_fija"], config["radio_metros"]
    )
    # Construir URL correcta (HTTPS en producción)
    base = str(request.base_url).rstrip("/")
    # Forzar HTTPS si viene por proxy
    forwarded_proto = request.headers.get("x-forwarded-proto", "")
    if forwarded_proto == "https":
        base = base.replace("http://", "https://")
    qr_url = f"{base}/app/checkin?token={token}"
    return {
        "qr_url": qr_url,
        "config": config,
        "expiracion_segundos": config["tiempo_expiracion"]
    }


@router.post("/api/asistencia/registrar")
async def registrar_asistencia(registro: RegistroAsistencia, request: Request):
    """Registra asistencia del técnico — requiere token JWT en Authorization"""
    from db import execute_write

    # ── Obtener username del JWT ──────────────────────────────────────────
    auth_header = request.headers.get("Authorization", "")
    username = None
    if auth_header.startswith("Bearer "):
        try:
            import os as _os
            from jose import jwt as _jwt
            token_jwt = auth_header[7:]
            payload_jwt = _jwt.decode(
                token_jwt,
                _os.getenv("SECRET_KEY", "carrier_secret_key_2024_change_in_production"),
                algorithms=["HS256"]
            )
            username = payload_jwt.get("sub")
        except Exception:
            pass
    if not username:
        raise HTTPException(status_code=401, detail="Token JWT inválido o ausente")

    # ── Validar token QR ──────────────────────────────────────────────────
    valido, payload, msg = validar_token(registro.token)
    if not valido:
        raise HTTPException(status_code=400, detail=msg)

    lat_fija = payload["lat"]
    lon_fija = payload["lon"]
    radio = payload["radio"]

    # ── Validar distancia ─────────────────────────────────────────────────
    distancia = calcular_distancia(registro.lat_tecnico, registro.lon_tecnico, lat_fija, lon_fija)
    if distancia > radio:
        raise HTTPException(status_code=400, detail=f"Fuera del área permitida. Distancia: {distancia:.1f}m (radio: {radio}m)")

    # ── Validar precisión GPS ─────────────────────────────────────────────
    if registro.gps_accuracy and registro.gps_accuracy > 100:
        raise HTTPException(status_code=400, detail=f"Precisión GPS muy baja: {registro.gps_accuracy:.1f}m. Espera a que mejore.")

    # ── Validar selfie ────────────────────────────────────────────────────
    if not registro.selfie_base64 or len(registro.selfie_base64) < 500:
        raise HTTPException(status_code=400, detail="Selfie obligatoria")

    # ── Evitar doble registro en el mismo día ─────────────────────────────
    from db import execute_read
    hoy = datetime.now().strftime("%Y-%m-%d")
    ya_registro = execute_read(
        "SELECT id FROM asistencia WHERE username=%s AND fecha=%s", (username, hoy)
    )
    if ya_registro:
        raise HTTPException(status_code=400, detail="Ya registraste asistencia hoy")

    # ── Guardar selfie ────────────────────────────────────────────────────
    fecha_str = datetime.now().strftime("%Y%m%d")
    exito, ruta_selfie, err_msg = guardar_selfie_sync(registro.selfie_base64, username, fecha_str)
    if not exito:
        # No bloquear el registro si falla guardar selfie, solo loguear
        ruta_selfie = None

    # ── Guardar en DB ─────────────────────────────────────────────────────
    hora_checkin = datetime.now().strftime("%H:%M:%S")
    try:
        execute_write("""
            INSERT INTO asistencia (
                username, fecha, hora_checkin, lat_fija, lon_fija, radio_metros,
                lat_tecnico, lon_tecnico, distancia_metros, gps_accuracy,
                selfie_path, aprobado
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            username, hoy, hora_checkin,
            lat_fija, lon_fija, radio,
            registro.lat_tecnico, registro.lon_tecnico, round(distancia, 1),
            registro.gps_accuracy, ruta_selfie, 1
        ))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar en DB: {str(e)}")

    return {
        "exito": True,
        "mensaje": f"✅ Asistencia registrada correctamente. Distancia: {distancia:.1f}m",
        "distancia": round(distancia, 1),
        "hora": hora_checkin
    }


@router.get("/api/asistencia/registros")
async def obtener_registros(fecha: Optional[str] = None, current_user=Depends(verify_token)):
    """Obtiene los registros de asistencia filtrados por fecha"""
    from db import execute_read
    if fecha:
        registros = execute_read(
            "SELECT * FROM asistencia WHERE fecha = %s ORDER BY hora_checkin DESC", (fecha,)
        )
    else:
        registros = execute_read(
            "SELECT * FROM asistencia WHERE fecha = CURDATE() ORDER BY hora_checkin DESC"
        )
    return registros if registros else []
