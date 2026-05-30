"""
routes.py — Rutas de asistencia
"""
import math
import os
import uuid
import base64
from datetime import datetime
from typing import Optional

import pytz
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from db import execute_read, execute_write, execute_write_with_id
from auth import verify_token

router = APIRouter(prefix="/api/asistencia", tags=["asistencia"])

TZ_TJ = pytz.timezone("America/Tijuana")

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
    radio_metros: int = 200

# ── Helpers ────────────────────────────────────────────────────────────────────
def _distancia_metros(lat1, lon1, lat2, lon2) -> float:
    lat1, lon1, lat2, lon2 = float(lat1), float(lon1), float(lat2), float(lon2)
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
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
    return {"lat_fija": 32.5027, "lon_fija": -117.0037, "radio_metros": 200}

# ── Directorio de selfies ──────────────────────────────────────────────────────
SELFIE_DIR = os.path.join(os.path.dirname(__file__), "selfies")
os.makedirs(SELFIE_DIR, exist_ok=True)

# ── Subir selfie ───────────────────────────────────────────────────────────────
@router.post("/selfie")
async def subir_selfie(
    file:     UploadFile = File(...),
    username: str        = Form(...),
    tipo:     str        = Form(...),
    fecha:    str        = Form(...),
    current_user=Depends(verify_token)
):
    """Guarda la selfie del técnico y devuelve la URL relativa."""
    try:
        contenido = await file.read()
        nombre    = f"{username}_{fecha}_{tipo}_{uuid.uuid4().hex[:8]}.jpg"
        ruta      = os.path.join(SELFIE_DIR, nombre)
        with open(ruta, "wb") as f:
            f.write(contenido)
        url = f"/api/asistencia/selfie/{nombre}"
        return {"ok": True, "url": url}
    except Exception as e:
        # Si falla el guardado no bloqueamos el checkin — devolvemos url vacía
        return {"ok": False, "url": None, "error": str(e)}

# ── Servir selfie ──────────────────────────────────────────────────────────────
@router.get("/selfie/{nombre}")
async def ver_selfie(nombre: str, current_user=Depends(verify_token)):
    from fastapi.responses import FileResponse
    ruta = os.path.join(SELFIE_DIR, nombre)
    if not os.path.exists(ruta):
        raise HTTPException(404, "Selfie no encontrada")
    return FileResponse(ruta, media_type="image/jpeg")

# ── Configuración ──────────────────────────────────────────────────────────────
@router.get("/configuracion")
def get_configuracion(current_user=Depends(verify_token)):
    return _get_config()

@router.post("/configuracion")
def save_configuracion(payload: ConfigPayload, current_user=Depends(verify_token)):
    existing = execute_read("SELECT id FROM asistencia_config LIMIT 1")
    if existing:
        execute_write(
            "UPDATE asistencia_config SET lat_fija=%s, lon_fija=%s, radio_metros=%s WHERE id=%s",
            (payload.lat_fija, payload.lon_fija, payload.radio_metros, existing[0]["id"])
        )
    else:
        execute_write(
            "INSERT INTO asistencia_config (lat_fija, lon_fija, radio_metros) VALUES (%s,%s,%s)",
            (payload.lat_fija, payload.lon_fija, payload.radio_metros)
        )
    return {"ok": True}

# ── Generar QR ─────────────────────────────────────────────────────────────────
@router.get("/generar-qr")
def generar_qr(current_user=Depends(verify_token)):
    cfg = _get_config()
    base_url = "https://app-83fd3b1b-5d1d-43fd-be37-63f56db0efe8.cleverapps.io"
    return {"qr_url": f"{base_url}/app/checkin", "config": cfg}

# ── Estado hoy ─────────────────────────────────────────────────────────────────
@router.get("/estado-hoy")
def estado_hoy(username: str = Query(...), fecha: str = Query(...), current_user=Depends(verify_token)):
    registros = execute_read(
        "SELECT tipo, hora_checkin FROM asistencia_registros WHERE username=%s AND fecha=%s",
        (username, fecha)
    )
    entrada = next((r for r in registros if r["tipo"] == "entrada"), None)
    salida  = next((r for r in registros if r["tipo"] == "salida"),  None)
    return {
        "tiene_entrada":     entrada is not None,
        "hora_entrada_real": entrada["hora_checkin"][:5] if entrada else None,
        "tiene_salida":      salida  is not None,
        "hora_salida_real":  salida["hora_checkin"][:5]  if salida  else None,
    }

# ── Checkin ────────────────────────────────────────────────────────────────────
@router.post("/checkin")
def checkin(payload: CheckinPayload, current_user=Depends(verify_token)):
    tipo = payload.tipo.lower().strip()
    if tipo not in ("entrada", "salida"):
        raise HTTPException(400, "Tipo debe ser 'entrada' o 'salida'")

    fecha = payload.fecha

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

    # ── Validar GPS ──
    cfg = _get_config()
    distancia_m = None
    aprobado = True

    if payload.lat is not None and payload.lon is not None:
        distancia_m = _distancia_metros(payload.lat, payload.lon, cfg["lat_fija"], cfg["lon_fija"])
        aprobado = distancia_m <= float(cfg["radio_metros"])

    hora_actual      = _hora_tj()
    retardo_min      = 0
    horas_trabajadas = None

    if tipo == "salida":
        ent_reg = execute_read(
            "SELECT hora_checkin FROM asistencia_registros WHERE username=%s AND fecha=%s AND tipo='entrada'",
            (payload.username, fecha)
        )
        if ent_reg:
            entrada_min      = _hhmm_to_min(ent_reg[0]["hora_checkin"][:5])
            salida_min       = _hhmm_to_min(hora_actual)
            horas_trabajadas = round(max(0, salida_min - entrada_min) / 60, 1)

    if tipo == "entrada":
        try:
            from datetime import date as _date
            horario = execute_read(
                "SELECT hora_entrada FROM horarios WHERE username=%s AND fecha=%s LIMIT 1",
                (payload.username, fecha)
            )
            if horario and horario[0].get("hora_entrada"):
                hora_prog_min = _hhmm_to_min(horario[0]["hora_entrada"][:5])
                hora_real_min = _hhmm_to_min(hora_actual)
                retardo_min   = max(0, hora_real_min - hora_prog_min)
        except Exception:
            retardo_min = 0

    # ── INSERT ──
    # Intentar incluir selfie_url si la columna existe
    try:
        execute_write(
            """INSERT INTO asistencia_registros
               (username, tipo, fecha, hora_checkin, lat, lon, precision_gps,
                distancia_metros, aprobado, retardo_min, selfie_url)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                payload.username, tipo, fecha, hora_actual,
                payload.lat, payload.lon, payload.precision_gps,
                round(distancia_m, 1) if distancia_m is not None else None,
                1 if aprobado else 0,
                retardo_min,
                payload.selfie_url,
            )
        )
    except Exception:
        # Fallback sin selfie_url (columna puede no existir todavía)
        execute_write(
            """INSERT INTO asistencia_registros
               (username, tipo, fecha, hora_checkin, lat, lon, precision_gps,
                distancia_metros, aprobado, retardo_min)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                payload.username, tipo, fecha, hora_actual,
                payload.lat, payload.lon, payload.precision_gps,
                round(distancia_m, 1) if distancia_m is not None else None,
                1 if aprobado else 0,
                retardo_min,
            )
        )

    return {
        "ok":               True,
        "tipo":             tipo,
        "hora_registro":    hora_actual,
        "aprobado":         aprobado,
        "distancia_metros": round(distancia_m, 1) if distancia_m is not None else None,
        "retardo_min":      retardo_min,
        "horas_trabajadas": horas_trabajadas,
    }

# ── Registros ──────────────────────────────────────────────────────────────────
@router.get("/registros")
def get_registros(
    fecha:    Optional[str] = Query(None),
    username: Optional[str] = Query(None),
    current_user=Depends(verify_token)
):
    sql    = "SELECT * FROM asistencia_registros WHERE 1=1"
    params = []
    if fecha:
        sql += " AND fecha=%s"; params.append(fecha)
    if username:
        sql += " AND username=%s"; params.append(username)
    sql += " ORDER BY fecha DESC, hora_checkin ASC"
    return execute_read(sql, tuple(params)) or []
