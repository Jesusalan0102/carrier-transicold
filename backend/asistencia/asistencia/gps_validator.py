# asistencia/asistencia/gps_validator.py
import math
from typing import Tuple, Optional


def calcular_distancia(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula la distancia en metros entre dos coordenadas GPS usando la fórmula de Haversine.
    """
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) * math.sin(dlat / 2) +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) * math.sin(dlon / 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def validar_ubicacion(
    lat_tecnico: float,
    lon_tecnico: float,
    lat_fija: float,
    lon_fija: float,
    radio_metros: float,
) -> Tuple[bool, float, str]:
    """
    Valida si la ubicación del técnico está dentro del radio permitido.
    Retorna: (dentro_del_radio, distancia_metros, mensaje)
    """
    distancia = calcular_distancia(lat_tecnico, lon_tecnico, lat_fija, lon_fija)
    dentro = distancia <= radio_metros

    if dentro:
        mensaje = f"✅ Ubicación válida. Distancia: {distancia:.1f} metros"
    else:
        mensaje = (
            f"❌ Ubicación fuera del área. Distancia: {distancia:.1f} metros "
            f"(límite: {radio_metros}m)"
        )

    return dentro, distancia, mensaje


def es_gps_preciso(
    accuracy: Optional[float],
    limite_metros: float = 50,
) -> Tuple[bool, str]:
    """
    Verifica si la señal GPS es lo suficientemente precisa.

    FIX Bug 4: cuando accuracy es None (navegador sin GPS físico, permisos
    denegados o dispositivo de escritorio) ya NO se bloquea el registro.
    Se devuelve True con un mensaje de advertencia para que el registro
    continúe y quede marcado como 'sin dato de precisión'.
    Si quieres volver al comportamiento bloqueante, cambia la línea
    'return True, ...' por 'return False, ...' en el bloque de accuracy None.
    """
    if accuracy is None:
        # Advertencia no bloqueante: el registro se guarda sin dato de precisión.
        return True, "⚠️ Sin dato de precisión GPS (se registra de todas formas)"

    if accuracy <= limite_metros:
        return True, f"✅ Precisión GPS aceptable: {accuracy:.1f}m"

    return False, (
        f"❌ Precisión GPS baja: {accuracy:.1f}m "
        f"(máximo permitido: {limite_metros}m)"
    )
