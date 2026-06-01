"""
routes.py — Rutas de asistencia (Actualizado Junio 2026)
"""
import math
import os
import uuid
from datetime import datetime
from typing import Optional

import pytz
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from db import execute_read, execute_write
from auth import verify_token

router = APIRouter(prefix="/api/asistencia", tags=["asistencia"])

TZ_TJ = pytz.timezone("America/Tijuana")
SELFIE_DIR = "static/selfies"
os.makedirs(SELFIE_DIR, exist_ok=True)

# ── Schemas ────────────────────────────────────────────────────────────────────
class CheckinPayload(BaseModel):
    username:      str
    tipo:          str
    fecha:         str
    lat:           Optional[float] = None
    lon:           Optional[float] = None
    precision_gps: Optional[float] = None
    selfie_url:    Optional[str]   = None

class ConfigPayload(BaseModel):
    lat_fija:     float
    lon_fija:     float
    radio_metros: int = 300   # ← Aumentado a 300m

# ── Helpers ────────────────────────────────────────────────────────────────────
def _distancia_metros(lat1, lon1, lat2, lon2) -> float:
    lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lon2 - lon1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def _hora_tj() -> str:
    return datetime.now(TZ_TJ).strftime("%H:%M")

def _hhmm_to_min(hhmm: str) -> int:
    h, m = hhmm.split(":")
    return int(h)*60 + int(m)

def _get_config():
    rows = execute_read("SELECT lat_fija, lon_fija, radio_metros FROM asistencia_config LIMIT 1")
    if rows:
        return rows[0]
    return {"lat_fija": 32.5027, "lon_fija": -117.0037, "radio_metros": 300}  # ← Default 300m

# ── Checkin Mejorado ───────────────────────────────────────────────────────────
@router.post("/checkin")
def checkin(payload: CheckinPayload, current_user=Depends(verify_token)):
    tipo = payload.tipo.lower().strip()
    if tipo not in ("entrada", "salida"):
        raise HTTPException(400, "Tipo debe ser 'entrada' o 'salida'")

    fecha = payload.fecha

    # Validar duplicados
    existente = execute_read(
        "SELECT id FROM asistencia_registros WHERE username=%s AND fecha=%s AND tipo=%s",
        (payload.username, fecha, tipo)
    )
    if existente:
        raise HTTPException(400, f"Ya registraste tu {tipo} hoy.")

    if tipo == "salida":
        entrada = execute_read(
            "SELECT id FROM asistencia_registros WHERE username=%s AND fecha=%s AND tipo='entrada'",
            (payload.username, fecha)
        )
        if not entrada:
            raise HTTPException(400, "Debes registrar tu entrada antes de la salida.")

    cfg = _get_config()
    distancia_m = None
    aprobado = True
    motivo_rechazo = None

    if payload.lat is not None and payload.lon is not None:
        distancia_m = _distancia_metros(payload.lat, payload.lon, cfg["lat_fija"], cfg["lon_fija"])
        aprobado = distancia_m <= float(cfg["radio_metros"])
        if not aprobado:
            motivo_rechazo = f"Fuera de rango. Distancia: {round(distancia_m, 1)}m (Radio: {cfg['radio_metros']}m)"
    else:
        motivo_rechazo = "GPS no disponible"

    hora_actual = _hora_tj()
    retardo_min = 0
    horas_trabajadas = None

    if tipo == "entrada":
        try:
            horario = execute_read(
                "SELECT hora_entrada FROM horarios WHERE username=%s AND fecha=%s LIMIT 1",
                (payload.username, fecha)
            )
            if horario and horario[0]["hora_entrada"]:
                hora_prog_min = _hhmm_to_min(horario[0]["hora_entrada"])
                hora_real_min = _hhmm_to_min(hora_actual)
                retardo_min = max(0, hora_real_min - hora_prog_min)
        except:
            retardo_min = 0

    if tipo == "salida":
        ent_reg = execute_read(
            "SELECT hora_checkin FROM asistencia_registros WHERE username=%s AND fecha=%s AND tipo='entrada'",
            (payload.username, fecha)
        )
        if ent_reg:
            entrada_min = _hhmm_to_min(ent_reg[0]["hora_checkin"][:5])
            salida_min = _hhmm_to_min(hora_actual)
            horas_trabajadas = round(max(0, salida_min - entrada_min) / 60, 1)

    # Insert con motivo_rechazo
    try:
        execute_write(
            """INSERT INTO asistencia_registros 
               (username, tipo, fecha, hora_checkin, lat, lon, precision_gps, 
                distancia_metros, aprobado, retardo_min, selfie_url, motivo_rechazo)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (payload.username, tipo, fecha, hora_actual,
             payload.lat, payload.lon, payload.precision_gps,
             round(distancia_m, 1) if distancia_m else None,
             1 if aprobado else 0,
             retardo_min,
             payload.selfie_url,
             motivo_rechazo)
        )
    except Exception:
        # Fallback sin motivo_rechazo
        execute_write(
            """INSERT INTO asistencia_registros 
               (username, tipo, fecha, hora_checkin, lat, lon, precision_gps, 
                distancia_metros, aprobado, retardo_min, selfie_url)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (payload.username, tipo, fecha, hora_actual,
             payload.lat, payload.lon, payload.precision_gps,
             round(distancia_m, 1) if distancia_m else None,
             1 if aprobado else 0,
             retardo_min,
             payload.selfie_url)
        )

    return {
        "ok": True,
        "tipo": tipo,
        "hora_registro": hora_actual,
        "aprobado": aprobado,
        "distancia_metros": round(distancia_m, 1) if distancia_m else None,
        "motivo_rechazo": motivo_rechazo,
        "retardo_min": retardo_min,
        "horas_trabajadas": horas_trabajadas
    }
