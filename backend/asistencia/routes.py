"""
backend/asistencia/routes.py
Rutas de Asistencia - Versión Mejorada (Junio 2026)
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
    radio_metros: int = 300  # Radio aumentado

# ── Helpers ────────────────────────────────────────────────────────────────────
def _distancia_metros(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000  # Radio de la Tierra en metros
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
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
    # Default actualizado
    return {"lat_fija": 32.5027, "lon_fija": -117.0037, "radio_metros": 300}

# ── Endpoint Principal ───────────────────────────────────────────────────────
@router.post("/checkin")
def checkin(payload: CheckinPayload, current_user=Depends(verify_token)):
    tipo = payload.tipo.lower().strip()
    if tipo not in ("entrada", "salida"):
        raise HTTPException(status_code=400, detail="Tipo debe ser 'entrada' o 'salida'")

    fecha = payload.fecha

    # Validar duplicados
    existente = execute_read(
        "SELECT id FROM asistencia_registros WHERE username=%s AND fecha=%s AND tipo=%s",
        (payload.username, fecha, tipo)
    )
    if existente:
        raise HTTPException(status_code=400, detail=f"Ya registraste tu {tipo} hoy.")

    # Validar flujo entrada → salida
    if tipo == "salida":
        entrada = execute_read(
            "SELECT id FROM asistencia_registros WHERE username=%s AND fecha=%s AND tipo='entrada'",
            (payload.username, fecha)
        )
        if not entrada:
            raise HTTPException(status_code=400, detail="Debes registrar tu entrada primero.")

    # ── Validación GPS ─────────────────────────────────────────────────────
    cfg = _get_config()
    distancia_m = None
    aprobado = True
    motivo_rechazo = None

    if payload.lat is not None and payload.lon is not None:
        distancia_m = _distancia_metros(payload.lat, payload.lon, cfg["lat_fija"], cfg["lon_fija"])
        aprobado = distancia_m <= float(cfg["radio_metros"])
        if not aprobado:
            motivo_rechazo = f"Fuera de rango. Distancia: {round(distancia_m, 1)}m (Radio permitido: {cfg['radio_metros']}m)"
    else:
        motivo_rechazo = "Coordenadas GPS no recibidas"

    hora_actual = _hora_tj()
    retardo_min = 0
    horas_trabajadas = None

    # Calcular retardo (entrada)
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

    # Calcular horas trabajadas (salida)
    if tipo == "salida":
        ent_reg = execute_read(
            "SELECT hora_checkin FROM asistencia_registros WHERE username=%s AND fecha=%s AND tipo='entrada'",
            (payload.username, fecha)
        )
        if ent_reg and ent_reg[0].get("hora_checkin"):
            entrada_min = _hhmm_to_min(ent_reg[0]["hora_checkin"])
            salida_min = _hhmm_to_min(hora_actual)
            horas_trabajadas = round(max(0, (salida_min - entrada_min) / 60), 1)

    # ── Guardar registro ───────────────────────────────────────────────────
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
        # Fallback sin motivo_rechazo (por si la columna aún no existe)
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
