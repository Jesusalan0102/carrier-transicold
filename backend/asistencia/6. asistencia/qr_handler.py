# asistencia/qr_handler.py
import hashlib
import time
import json
import base64
from typing import Tuple, Optional, Dict, Any

QR_EXPIRATION_SECONDS = 300

def generar_token_seguro(lat: float, lon: float, radio: int) -> str:
    """Genera un token único para el QR que incluye timestamp y hash de seguridad."""
    timestamp = int(time.time())
    payload = {
        "lat": lat,
        "lon": lon,
        "radio": radio,
        "exp": timestamp + QR_EXPIRATION_SECONDS,
        "created": timestamp
    }
    data_str = f"{lat}:{lon}:{radio}:{payload['exp']}"
    signature = hashlib.sha256(data_str.encode()).hexdigest()[:16]
    payload["sig"] = signature
    return base64.b64encode(json.dumps(payload).encode()).decode()


def validar_y_decodificar_token(token: str) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """Valida y decodifica el token del QR."""
    try:
        decoded = base64.b64decode(token).decode()
        payload = json.loads(decoded)
        
        exp = payload.get('exp', 0)
        if exp < time.time():
            return False, None, "El código QR ha expirado. Solicita uno nuevo al administrador."
        
        lat = payload.get('lat')
        lon = payload.get('lon')
        radio = payload.get('radio')
        signature = payload.get('sig', '')
        
        data_str = f"{lat}:{lon}:{radio}:{exp}"
        expected_sig = hashlib.sha256(data_str.encode()).hexdigest()[:16]
        
        if signature != expected_sig:
            return False, None, "Código QR inválido o manipulado."
        
        return True, payload, "QR válido"
        
    except Exception as e:
        return False, None, f"Error al leer QR: {str(e)}"


def generar_url_qr(base_url: str, lat: float, lon: float, radio: int) -> str:
    """Genera la URL completa para el QR."""
    token = generar_token_seguro(lat, lon, radio)
    return f"{base_url}/app/checkin?token={token}"
