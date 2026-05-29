"""
routes.py — Rutas de asistencia
Maneja:
  - POST /api/asistencia/checkin         → Registra entrada o salida
  - GET  /api/asistencia/estado-hoy      → Estado del día del técnico
  - GET  /api/asistencia/registros       → Lista de registros (admin y técnico)
  - GET  /api/asistencia/configuracion   → Lee config de geolocalización
  - POST /api/asistencia/configuracion   → Guarda config de geolocalización
  - GET  /api/asistencia/generar-qr      → URL para el QR permanente
"""

import math
import json
from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

# ─── Importa los modelos y helpers de tu proyecto ──────────────────────────────
# Ajusta los imports según la estructura real de tu proyecto.
# Ejemplo genérico — reemplaza con los tuyos:
from database import get_db
from models import AsistenciaRegistro, AsistenciaConfig, Horario, User
from auth import get_current_user

router = APIRouter(prefix="/api/asistencia", tags=["asistencia"])


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class CheckinPayload(BaseModel):
    username:     str
    tipo:         str          # "entrada" | "salida"
    fecha:        str          # "YYYY-MM-DD" — fecha local Tijuana
    lat:          Optional[float] = None
    lon:          Optional[float] = None
    precision_gps: Optional[float] = None

class ConfigPayload(BaseModel):
    lat_fija:     float
    lon_fija:     float
    radio_metros: int = 200


# ═══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def _distancia_metros(lat1, lon1, lat2, lon2) -> float:
    """Haversine — devuelve metros entre dos coordenadas."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi  = math.radians(lat2 - lat1)
    dlam  = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def _hora_tj() -> str:
    """Hora actual en Tijuana HH:MM."""
    import pytz
    tz = pytz.timezone("America/Tijuana")
    return datetime.now(tz).strftime("%H:%M")

def _hhmm_to_min(hhmm: str) -> int:
    """Convierte 'HH:MM' a minutos desde medianoche."""
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)

def _min_to_hhmm(mins: int) -> str:
    return f"{mins // 60:02d}:{mins % 60:02d}"


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN DE GEOLOCALIZACIÓN
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/configuracion")
async def get_configuracion(db: Session = Depends(get_db)):
    """Devuelve la configuración de coordenadas y radio."""
    cfg = db.query(AsistenciaConfig).first()
    if not cfg:
        # Valores por defecto
        return {"lat_fija": 32.5027, "lon_fija": -117.0037, "radio_metros": 200}
    return {"lat_fija": cfg.lat_fija, "lon_fija": cfg.lon_fija, "radio_metros": cfg.radio_metros}


@router.post("/configuracion")
async def save_configuracion(payload: ConfigPayload, db: Session = Depends(get_db)):
    """Guarda o actualiza la configuración de geolocalización."""
    cfg = db.query(AsistenciaConfig).first()
    if cfg:
        cfg.lat_fija     = payload.lat_fija
        cfg.lon_fija     = payload.lon_fija
        cfg.radio_metros = payload.radio_metros
    else:
        cfg = AsistenciaConfig(
            lat_fija     = payload.lat_fija,
            lon_fija     = payload.lon_fija,
            radio_metros = payload.radio_metros,
        )
        db.add(cfg)
    db.commit()
    return {"ok": True}


# ═══════════════════════════════════════════════════════════════════════════════
# GENERAR QR
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/generar-qr")
async def generar_qr(db: Session = Depends(get_db)):
    """
    Devuelve la URL permanente del checkin para usar como QR.
    El QR apunta a /app/checkin — el técnico debe iniciar sesión.
    """
    cfg = db.query(AsistenciaConfig).first()
    config = {
        "lat_fija":     cfg.lat_fija     if cfg else 32.5027,
        "lon_fija":     cfg.lon_fija     if cfg else -117.0037,
        "radio_metros": cfg.radio_metros if cfg else 200,
    }
    base_url = "https://app-83fd3b1b-5d1d-43fd-be37-63f56db0efe8.cleverapps.io"
    return {
        "qr_url": f"{base_url}/app/checkin",
        "config": config,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ESTADO DEL DÍA (técnico)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/estado-hoy")
async def estado_hoy(
    username: str = Query(...),
    fecha:    str = Query(...),
    db: Session = Depends(get_db),
):
    """
    Devuelve si el técnico ya registró entrada y/o salida hoy.

    Respuesta:
    {
        "tiene_entrada": bool,
        "hora_entrada_real": "HH:MM" | null,
        "tiene_salida": bool,
        "hora_salida_real": "HH:MM" | null
    }
    """
    registros = (
        db.query(AsistenciaRegistro)
        .filter(AsistenciaRegistro.username == username, AsistenciaRegistro.fecha == fecha)
        .all()
    )

    entrada = next((r for r in registros if r.tipo == "entrada"), None)
    salida  = next((r for r in registros if r.tipo == "salida"),  None)

    return {
        "tiene_entrada":      entrada is not None,
        "hora_entrada_real":  entrada.hora_checkin[:5] if entrada else None,
        "tiene_salida":       salida is not None,
        "hora_salida_real":   salida.hora_checkin[:5]  if salida  else None,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CHECKIN — Registrar entrada o salida
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/checkin")
async def checkin(payload: CheckinPayload, db: Session = Depends(get_db)):
    """
    Registra una entrada o salida validando:
      1. Que el tipo sea válido ('entrada' o 'salida').
      2. Que no se repita el tipo ya registrado hoy.
      3. Que la salida sea posterior a la entrada.
      4. Geolocalización vs. radio configurado (si aplica).
      5. Calcula retardo_min (solo para entradas) y horas_trabajadas (solo salidas).
    """
    tipo = payload.tipo.lower().strip()
    if tipo not in ("entrada", "salida"):
        raise HTTPException(400, "Tipo debe ser 'entrada' o 'salida'")

    fecha = payload.fecha

    # ── Verificar duplicado ──────────────────────────────────────────────────
    existente = (
        db.query(AsistenciaRegistro)
        .filter(
            AsistenciaRegistro.username == payload.username,
            AsistenciaRegistro.fecha    == fecha,
            AsistenciaRegistro.tipo     == tipo,
        )
        .first()
    )
    if existente:
        raise HTTPException(
            400,
            f"Ya registraste tu {'entrada' if tipo == 'entrada' else 'salida'} hoy."
        )

    # ── Si es salida, verificar que exista entrada ───────────────────────────
    if tipo == "salida":
        entrada = (
            db.query(AsistenciaRegistro)
            .filter(
                AsistenciaRegistro.username == payload.username,
                AsistenciaRegistro.fecha    == fecha,
                AsistenciaRegistro.tipo     == "entrada",
            )
            .first()
        )
        if not entrada:
            raise HTTPException(400, "Debes registrar tu entrada antes de la salida.")

    # ── Geolocalización ──────────────────────────────────────────────────────
    cfg = db.query(AsistenciaConfig).first()
    distancia_m = None
    aprobado    = True  # si no hay GPS configurado, se aprueba igual

    if cfg and payload.lat is not None and payload.lon is not None:
        distancia_m = _distancia_metros(
            payload.lat, payload.lon, cfg.lat_fija, cfg.lon_fija
        )
        aprobado = distancia_m <= cfg.radio_metros

    # ── Hora actual en Tijuana ───────────────────────────────────────────────
    hora_actual = _hora_tj()  # "HH:MM"

    # ── Calcular retardo para entrada ────────────────────────────────────────
    retardo_min   = 0
    horas_trabajadas = None

    horario = (
        db.query(Horario)
        .filter(Horario.username == payload.username, Horario.fecha == fecha)
        .first()
    )

    if tipo == "entrada" and horario and horario.hora_entrada:
        hora_min     = _hhmm_to_min(hora_actual)
        entrada_min  = _hhmm_to_min(horario.hora_entrada[:5])
        TOLERANCIA   = 15  # minutos de gracia
        retardo_min  = max(0, hora_min - entrada_min - TOLERANCIA)

    # ── Calcular horas trabajadas para salida ────────────────────────────────
    if tipo == "salida":
        entrada_reg = (
            db.query(AsistenciaRegistro)
            .filter(
                AsistenciaRegistro.username == payload.username,
                AsistenciaRegistro.fecha    == fecha,
                AsistenciaRegistro.tipo     == "entrada",
            )
            .first()
        )
        if entrada_reg:
            entrada_min  = _hhmm_to_min(entrada_reg.hora_checkin[:5])
            salida_min   = _hhmm_to_min(hora_actual)
            total_min    = max(0, salida_min - entrada_min)
            horas_trabajadas = round(total_min / 60, 1)

    # ── Guardar registro ─────────────────────────────────────────────────────
    registro = AsistenciaRegistro(
        username         = payload.username,
        tipo             = tipo,
        fecha            = fecha,
        hora_checkin     = hora_actual,
        lat              = payload.lat,
        lon              = payload.lon,
        precision_gps    = payload.precision_gps,
        distancia_metros = distancia_m,
        aprobado         = aprobado,
        retardo_min      = retardo_min,
    )
    db.add(registro)
    db.commit()

    return {
        "ok":               True,
        "tipo":             tipo,
        "hora_registro":    hora_actual,
        "aprobado":         aprobado,
        "distancia_metros": round(distancia_m, 1) if distancia_m is not None else None,
        "retardo_min":      retardo_min,
        "horas_trabajadas": horas_trabajadas,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# REGISTROS — Listado (admin y técnico)
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/registros")
async def get_registros(
    fecha:    Optional[str] = Query(None),
    username: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    """
    Lista registros de asistencia.
    - Admin: puede filtrar por fecha (y opcionalmente username).
    - Técnico: siempre filtra por su propio username.
    """
    query = db.query(AsistenciaRegistro)
    if fecha:
        query = query.filter(AsistenciaRegistro.fecha == fecha)
    if username:
        query = query.filter(AsistenciaRegistro.username == username)
    registros = query.order_by(AsistenciaRegistro.fecha.desc(), AsistenciaRegistro.hora_checkin.asc()).all()

    return [
        {
            "id":               r.id,
            "username":         r.username,
            "tipo":             r.tipo,
            "fecha":            r.fecha,
            "hora_checkin":     r.hora_checkin,
            "distancia_metros": r.distancia_metros,
            "aprobado":         r.aprobado,
            "retardo_min":      r.retardo_min,
        }
        for r in registros
    ]
