"""
backend/asistencia/routes.py
Rutas de Asistencia - Versión Mejorada (Junio 2026)
Adaptado para inyectar dinámicamente los motivos y distancias estructuradas de geofencing
"""

import math
import os
from datetime import datetime
from typing import Optional

import pytz
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from db import execute_read, execute_write
from auth import verify_token

router = APIRouter(prefix="/api/asistencia", tags=["asistencia"])

TZ_TJ = pytz.timezone("America/Tijuana")

# ── Schemas ────────────────────────────────────────────────────────────────────
class CheckinPayload(BaseModel):
    username: str
    tipo: str
    fecha: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    precision_gps: Optional[float] = None
    selfie_url: Optional[str] = None

class ConfigPayload(BaseModel):
    lat_fija: float
    lon_fija: float
    radio_metros: int = 300

# ── Helpers ────────────────────────────────────────────────────────────────────
def _distancia_metros(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000  # Radio de la Tierra en metros
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - Math.radians(lat1)) # Asegurando compatibilidad limpia
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def _hora_tj() -> str:
    return datetime.now(TZ_TJ).strftime("%H:%M")

def _hhmm_to_min(hhmm: str) -> int:
    if not hhmm:
        return 0
    h, m = map(int, hhmm.split(":")[:2])
    return h * 60 + m

def _get_config():
    rows = execute_read("SELECT lat_fija, lon_fija, radio_metros FROM asistencia_config LIMIT 1")
    if rows:
        return rows[0]
    return {"lat_fija": 32.5027, "lon_fija": -117.0037, "radio_metros": 300}

# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/registros/{username}/{fecha}")
def obtener_registros_dia(username: str, fecha: str, current_user=Depends(verify_token)):
    """
    Retorna los registros del empleado para pintarlos dinámicamente en la interfaz limpia.
    """
    query = """
        SELECT tipo, hora_checkin, distancia_metros, aprobado, motivo_rechazo 
        FROM asistencia_registros 
        WHERE username = %s AND fecha = %s 
        ORDER BY hora_checkin DESC
    """
    rows = execute_read(query, (username, fecha))
    return {"ok": True, "registros": rows or []}


@router.post("/checkin")
def checkin(payload: CheckinPayload, current_user=Depends(verify_token)):
    tipo = payload.tipo.lower().strip()
    if tipo not in ("entrada", "salida"):
        raise HTTPException(status_code=400, detail="Tipo debe ser 'entrada' o 'salida'")

    fecha = payload.fecha

    # Validar duplicados de intentos Exitosos (permite reintentar si el previo fue rechazado)
    existente = execute_read(
        "SELECT id FROM asistencia_registros WHERE username=%s AND fecha=%s AND tipo=%s AND aprobado = 1",
        (payload.username, fecha, tipo)
    )
    if existente:
        raise HTTPException(status_code=400, detail=f"Ya cuentas con una {tipo} válida registrada hoy.")

    # Validar flujo entrada → salida
    if tipo == "salida":
        entrada = execute_read(
            "SELECT id FROM asistencia_registros WHERE username=%s AND fecha=%s AND tipo='entrada' AND aprobado = 1",
            (payload.username, fecha)
        )
        if not entrada:
            raise HTTPException(status_code=400, detail="Debes registrar tu entrada aprobada primero.")

    # ── Validación de Geofencing (Perímetro) ──────────────────────────────────
    cfg = _get_config()
    distancia_m = None
    aprobado = True
    motivo_rechazo = None

    if payload.lat is not None and payload.lon is not None:
        distancia_m = _distancia_metros(payload.lat, payload.lon, cfg["lat_fija"], cfg["lon_fija"])
        aprobado = distancia_m <= float(cfg["radio_metros"])
        if not aprobado:
            distancia_km = round(distancia_m / 1000, 1)
            if distancia_m >= 1000:
                motivo_rechazo = f"A {distancia_km:,} km de la sucursal"
            else:
                motivo_rechazo = f"A {round(distancia_m)} m de la sucursal"
    else:
        aprobado = False
        motivo_rechazo = "Coordenadas GPS no recibidas"

    hora_actual = _hora_tj()
    retardo_min = 0
    horas_trabajadas = None

    # Calcular retraso (entrada)
    if tipo == "entrada":
        try:
            horario = execute_read(
                "SELECT hora_entrada FROM horarios WHERE username=%s AND fecha=%s LIMIT 1",
                (payload.username, fecha)
            )
            if horario and horario[0].get("hora_entrada"):
                hora_prog = _hhmm_to_min(horario[0]["hora_entrada"])
                hora_real = _hhmm_to_min(hora_actual)
                retardo_min = max(0, hora_real - hora_prog)
        except Exception:
            retardo_min = 0

    # Calcular horas de jornada (salida)
    if tipo == "salida" and aprobado:
        ent_reg = execute_read(
            "SELECT hora_checkin FROM asistencia_registros WHERE username=%s AND fecha=%s AND tipo='entrada' AND aprobado = 1",
            (payload.username, fecha)
        )
        if ent_reg and ent_reg[0].get("hora_checkin"):
            entrada_min = _hhmm_to_min(ent_reg[0]["hora_checkin"])
            salida_min = _hhmm_to_min(hora_actual)
            horas_trabajadas = round(max(0, (salida_min - entrada_min) / 60), 1)

    # ── Almacenamiento Seguro en DB ───────────────────────────────────────────
    try:
        execute_write(
            """INSERT INTO asistencia_registros 
               (username, tipo, fecha, hora_checkin, lat, lon, precision_gps, 
                distancia_metros, aprobado, retardo_min, selfie_url, motivo_rechazo)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                payload.username, tipo, fecha, hora_actual,
                payload.lat, payload.lon, payload.precision_gps,
                round(distancia_m, 1) if distancia_m is not None else None,
                1 if aprobado else 0,
                retardo_min,
                payload.selfie_url,
                motivo_rechazo
            )
        )
    except Exception:
        # Fallback por si la estructura SQL inicial no incluye la columna string de rechazo
        execute_write(
            """INSERT INTO asistencia_registros 
               (username, tipo, fecha, hora_checkin, lat, lon, precision_gps, 
                distancia_metros, aprobado, retardo_min, selfie_url)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                payload.username, tipo, fecha, hora_actual,
                payload.lat, payload.lon, payload.precision_gps,
                round(distancia_m, 1) if distancia_m is not None else None,
                1 if aprobado else 0,
                retardo_min,
                payload.selfie_url
            )
        )

    return {
        "ok": True,
        "tipo": tipo,
        "hora_registro": hora_actual,
        "aprobado": aprobado,
        "distancia_metros": round(distancia_m, 1) if distancia_m is not None else None,
        "motivo_rechazo": motivo_rechazo,
        "retardo_min": retardo_min,
        "horas_trabajadas": horas_trabajadas
    }
