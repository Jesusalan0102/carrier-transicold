# backend/asistencia/routes.py
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, date
import json
import os
import aiofiles
import uuid
import hashlib
import base64
import math

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
_configuracion_asistencia = {
    "lat_fija": 32.5027,
    "lon_fija": -117.0037,
    "radio_metros": 200,
    "tiempo_expiracion": 300
}

BASE_SELFIES_DIR = "storage/selfies"
os.makedirs(BASE_SELFIES_DIR, exist_ok=True)


# ==================== FUNCIONES AUXILIARES ====================
def calcular_distancia(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + \
        math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
        math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


def generar_token_seguro(lat: float, lon: float, radio: int) -> str:
    timestamp = int(datetime.now().timestamp())
    exp = timestamp + _configuracion_asistencia["tiempo_expiracion"]
    payload = {"lat": lat, "lon": lon, "radio": radio, "exp": exp}
    data_str = f"{lat}:{lon}:{radio}:{exp}"
    signature = hashlib.sha256(data_str.encode()).hexdigest()[:16]
    payload["sig"] = signature
    return base64.b64encode(json.dumps(payload).encode()).decode()


def validar_token(token: str):
    try:
        decoded = base64.b64decode(token).decode()
        payload = json.loads(decoded)
        if payload.get("exp", 0) < datetime.now().timestamp():
            return False, None, "QR expirado"
        expected_sig = hashlib.sha256(f"{payload['lat']}:{payload['lon']}:{payload['radio']}:{payload['exp']}".encode()).hexdigest()[:16]
        if payload.get("sig") != expected_sig:
            return False, None, "QR inválido"
        return True, payload, "OK"
    except:
        return False, None, "QR inválido"


def decode_base64_image(base64_string: str):
    if ',' in base64_string:
        base64_string = base64_string.split(',')[1]
    return base64.b64decode(base64_string)


async def guardar_selfie(base64_image: str, username: str, fecha: str):
    image_bytes = decode_base64_image(base64_image)
    if not image_bytes or len(image_bytes) < 5000:
        return False, None, "Imagen inválida o muy pequeña"
    unique_id = str(uuid.uuid4())[:8]
    filename = f"{username}_{fecha}_{unique_id}.jpg"
    filepath = os.path.join(BASE_SELFIES_DIR, filename)
    async with aiofiles.open(filepath, 'wb') as f:
        await f.write(image_bytes)
    return True, f"storage/selfies/{filename}", "OK"


# ==================== ENDPOINTS ====================
@router.get("/api/asistencia/configuracion")
async def get_configuracion():
    """Obtiene la configuración actual de asistencia"""
    return _configuracion_asistencia


@router.post("/api/asistencia/configuracion")
async def set_configuracion(config: ConfiguracionAsistencia):
    """Actualiza la configuración de asistencia"""
    global _configuracion_asistencia
    _configuracion_asistencia = config.dict()
    return {"mensaje": "Configuración actualizada", "config": _configuracion_asistencia}


@router.get("/api/asistencia/generar-qr")
async def generar_qr(request: Request):
    """Genera el QR de asistencia con la configuración actual"""
    config = _configuracion_asistencia
    token = generar_token_seguro(config["lat_fija"], config["lon_fija"], config["radio_metros"])
    qr_url = f"{str(request.base_url).rstrip('/')}/app/checkin?token={token}"
    print(f"QR generado: {qr_url}")  # Log para depuración
    return {
        "qr_url": qr_url, 
        "config": config, 
        "expiracion_segundos": config["tiempo_expiracion"]
    }


@router.post("/api/asistencia/registrar")
async def registrar_asistencia(registro: RegistroAsistencia, request: Request):
    """Registra la asistencia del técnico con validación de ubicación y selfie"""
    from db import execute_write
    
    # Validar token
    valido, payload, msg = validar_token(registro.token)
    if not valido:
        raise HTTPException(status_code=400, detail=msg)
    
    lat_fija = payload["lat"]
    lon_fija = payload["lon"]
    radio = payload["radio"]
    
    # Validar distancia
    distancia = calcular_distancia(registro.lat_tecnico, registro.lon_tecnico, lat_fija, lon_fija)
    dentro_radio = distancia <= radio
    
    if not dentro_radio:
        raise HTTPException(status_code=400, detail=f"Fuera del área permitida. Distancia: {distancia:.1f}m")
    
    # Validar precisión GPS
    if registro.gps_accuracy and registro.gps_accuracy > 50:
        raise HTTPException(status_code=400, detail=f"Precisión GPS baja: {registro.gps_accuracy:.1f}m")
    
    # Validar selfie
    if not registro.selfie_base64 or len(registro.selfie_base64) < 1000:
        raise HTTPException(status_code=400, detail="Selfie obligatoria")
    
    # Obtener usuario
    username = getattr(request.state, 'username', None)
    if not username:
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            try:
                import jwt
                token_jwt = auth_header[7:]
                payload_jwt = jwt.decode(token_jwt, options={"verify_signature": False})
                username = payload_jwt.get('sub')
            except:
                pass
    
    if not username:
        username = "tecnico_desconocido"
    
    # Guardar selfie
    fecha_str = datetime.now().strftime("%Y%m%d")
    exito, ruta_selfie, _ = await guardar_selfie(registro.selfie_base64, username, fecha_str)
    if not exito:
        raise HTTPException(status_code=500, detail="Error al guardar selfie")
    
    # Guardar en DB
    try:
        execute_write("""
            INSERT INTO asistencia (
                username, fecha, hora, lat_fija, lon_fija, radio_metros,
                lat_tecnico, lon_tecnico, distancia_m, gps_accuracy,
                selfie_path, dentro_radio, fecha_registro
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            username,
            datetime.now().strftime("%Y-%m-%d"),
            datetime.now().strftime("%H:%M:%S"),
            lat_fija, lon_fija, radio,
            registro.lat_tecnico, registro.lon_tecnico, distancia,
            registro.gps_accuracy,
            ruta_selfie,
            1 if dentro_radio else 0,
            datetime.now().isoformat()
        ))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al guardar: {str(e)}")
    
    return {
        "exito": True,
        "mensaje": f"Asistencia registrada. Distancia: {distancia:.1f}m",
        "distancia": round(distancia, 1),
        "dentro_radio": dentro_radio
    }


@router.get("/api/asistencia/registros")
async def obtener_registros(fecha: Optional[str] = None):
    """Obtiene los registros de asistencia para una fecha específica"""
    from db import execute_read
    
    if fecha:
        registros = execute_read("SELECT * FROM asistencia WHERE fecha = %s ORDER BY hora DESC", (fecha,))
    else:
        registros = execute_read("SELECT * FROM asistencia WHERE fecha = CURDATE() ORDER BY hora DESC")
    
    return registros
