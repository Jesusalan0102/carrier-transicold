"""
horarios_routes.py — Rutas de horarios semanales
Migrado de SQLAlchemy a db.py (pymysql directo) para consistencia con el resto de la app.

Endpoints:
  GET  /api/horarios/        → Horarios de la semana (todos)
  POST /api/horarios/        → Guarda horarios (batch upsert)
  GET  /api/horarios/hoy     → Horario de un técnico en una fecha concreta
  GET  /api/horarios/mios    → *** NUEVO *** Horarios del técnico logueado
  GET  /api/horarios/resumen → Resumen semanal
"""

from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from auth import verify_token
from db import execute_read, execute_write

# ====================== TIMEZONE TIJUANA ======================
import zoneinfo
from datetime import datetime

TZ_TJ = zoneinfo.ZoneInfo("America/Tijuana")


def ahora_tijuana():
    """Devuelve la hora actual en Tijuana"""
    return datetime.now(TZ_TJ)


router = APIRouter(prefix="/api/horarios", tags=["horarios"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class HorarioItem(BaseModel):
    username: str
    fecha: str           # "YYYY-MM-DD"
    semana: str          # "YYYY-MM-DD" (lunes de esa semana)
    hora_entrada: Optional[str] = None   # "HH:MM"
    hora_salida: Optional[str] = None    # "HH:MM"


class HorariosBatch(BaseModel):
    registros: List[HorarioItem]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _hhmm_to_min(hhmm: Optional[str]) -> Optional[int]:
    if not hhmm:
        return None
    try:
        h, m = hhmm[:5].split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return None


# ── GET /api/horarios/ ─────────────────────────────────────────────────────────

@router.get("/")
def get_horarios(
    semana: Optional[str] = Query(None),
    current_user=Depends(verify_token)
):
    """Devuelve todos los horarios de una semana (para administradores)"""
    if semana:
        rows = execute_read(
            "SELECT id, username, fecha, semana, hora_entrada, hora_salida "
            "FROM horarios WHERE semana=%s ORDER BY fecha, username",
            (semana,)
        )
    else:
        rows = execute_read(
            "SELECT id, username, fecha, semana, hora_entrada, hora_salida "
            "FROM horarios ORDER BY fecha DESC, username LIMIT 100"
        )

    return [
        {
            "id": r["id"],
            "username": r["username"],
            "fecha": r["fecha"].isoformat() if hasattr(r["fecha"], "isoformat") else str(r["fecha"]),
            "semana": r["semana"].isoformat() if hasattr(r["semana"], "isoformat") else str(r["semana"]),
            "hora_entrada": r["hora_entrada"],
            "hora_salida": r["hora_salida"],
        }
        for r in (rows or [])
    ]


# ── GET /api/horarios/mios  ←←← ESTE ES EL NUEVO ENDPOINT PARA TÉCNICOS ──

@router.get("/mios")
def get_mis_horarios(
    semana: Optional[str] = Query(None),
    current_user=Depends(verify_token)
):
    """Devuelve SOLO los horarios del técnico que está logueado"""
    username = current_user["username"]

    if semana:
        rows = execute_read(
            """SELECT id, fecha, semana, hora_entrada, hora_salida 
               FROM horarios 
               WHERE username = %s AND semana = %s 
               ORDER BY fecha""",
            (username, semana)
        )
    else:
        # Últimos 14 días por defecto
        rows = execute_read(
            """SELECT id, fecha, semana, hora_entrada, hora_salida 
               FROM horarios 
               WHERE username = %s 
               ORDER BY fecha DESC LIMIT 14""",
            (username,)
        )

    return [
        {
            "id": r["id"],
            "fecha": str(r["fecha"]),
            "semana": str(r["semana"]),
            "hora_entrada": r["hora_entrada"],
            "hora_salida": r["hora_salida"],
        }
        for r in (rows or [])
    ]


# ── POST /api/horarios/ ────────────────────────────────────────────────────────

@router.post("/")
def save_horarios(payload: HorariosBatch, current_user=Depends(verify_token)):
    """Guarda o actualiza (upsert) los horarios de una semana."""
    if current_user["role"] not in ("admin",):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Solo administradores")

    guardados = 0
    eliminados = 0

    for item in payload.registros:
        entrada = (item.hora_entrada or "").strip()
        salida = (item.hora_salida or "").strip()

        existente = execute_read(
            "SELECT id FROM horarios WHERE username=%s AND fecha=%s",
            (item.username, item.fecha)
        )

        if not entrada and not salida:
            # Día libre — borrar si existía
            if existente:
                execute_write(
                    "DELETE FROM horarios WHERE username=%s AND fecha=%s",
                    (item.username, item.fecha)
                )
                eliminados += 1
        else:
            if existente:
                execute_write(
                    "UPDATE horarios SET hora_entrada=%s, hora_salida=%s, semana=%s "
                    "WHERE username=%s AND fecha=%s",
                    (entrada or None, salida or None, item.semana,
                     item.username, item.fecha)
                )
            else:
                execute_write(
                    "INSERT INTO horarios (username, fecha, semana, hora_entrada, hora_salida) "
                    "VALUES (%s,%s,%s,%s,%s)",
                    (item.username, item.fecha, item.semana,
                     entrada or None, salida or None)
                )
            guardados += 1

    return {"ok": True, "guardados": guardados, "eliminados": eliminados}


# ── GET /api/horarios/hoy ──────────────────────────────────────────────────────

@router.get("/hoy")
def get_horario_hoy(
    username: str = Query(...),
    fecha: str = Query(...),
    current_user=Depends(verify_token)
):
    """Devuelve el horario de un técnico para una fecha específica."""
    rows = execute_read(
        "SELECT hora_entrada, hora_salida FROM horarios "
        "WHERE username=%s AND fecha=%s LIMIT 1",
        (username, fecha)
    )
    if not rows:
        return {"horario": None}
    h = rows[0]
    return {
        "horario": {
            "hora_entrada": h["hora_entrada"],
            "hora_salida": h["hora_salida"],
        }
    }


# ── GET /api/horarios/resumen ──────────────────────────────────────────────────

@router.get("/resumen")
def get_resumen(
    semana: str = Query(...),
    current_user=Depends(verify_token)
):
    if current_user["role"] not in ("admin", "visor"):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Solo administradores o visores")

    try:
        lunes = date.fromisoformat(semana)
    except ValueError:
        return []

    fechas = [(lunes + timedelta(days=i)).isoformat() for i in range(6)]
    placeholders = ",".join(["%s"] * len(fechas))

    # Horarios programados
    horarios_raw = execute_read(
        "SELECT username, fecha, hora_entrada, hora_salida "
        "FROM horarios WHERE semana=%s",
        (semana,)
    ) or []

    horarios_map = {}
    for h in horarios_raw:
        fecha_str = h["fecha"].isoformat() if hasattr(h["fecha"], "isoformat") else str(h["fecha"])
        horarios_map[(h["username"], fecha_str)] = h

    # Registros reales
    registros_raw = execute_read(
        f"SELECT username, fecha, tipo, hora_checkin, distancia_metros, aprobado, retardo_min "
        f"FROM asistencia_registros WHERE fecha IN ({placeholders}) ORDER BY hora_checkin",
        tuple(fechas)
    ) or []

    reg_map = {}
    for r in registros_raw:
        fecha_str = r["fecha"].isoformat() if hasattr(r["fecha"], "isoformat") else str(r["fecha"])
        key = (r["username"], fecha_str, r["tipo"])
        reg_map[key] = r

    # Construir resultado
    tecnicos = {h["username"] for h in horarios_raw} | {r["username"] for r in registros_raw}
    resultado = []

    for username in sorted(tecnicos):
        for fecha in fechas:
            horario = horarios_map.get((username, fecha))
            entrada = reg_map.get((username, fecha, "entrada"))
            salida = reg_map.get((username, fecha, "salida"))

            if not horario and not entrada and not salida:
                continue

            e_prog = _hhmm_to_min(horario["hora_entrada"] if horario else None)
            s_prog = _hhmm_to_min(horario["hora_salida"] if horario else None)
            e_real = _hhmm_to_min(entrada["hora_checkin"] if entrada else None)
            s_real = _hhmm_to_min(salida["hora_checkin"] if salida else None)

            retardo_min = max(0, e_real - e_prog - 15) if e_prog is not None and e_real is not None else 0
            salida_anticipada_min = max(0, s_prog - s_real) if s_prog is not None and s_real is not None else 0

            horas_trabajadas = round(max(0, s_real - e_real) / 60, 2) if e_real is not None and s_real is not None else None

            if not horario or (not horario.get("hora_entrada") and not horario.get("hora_salida")):
                estado = "libre"
            elif not entrada and not salida:
                estado = "ausente"
            elif entrada and not salida:
                estado = "sin_salida"
            elif not entrada and salida:
                estado = "sin_entrada"
            else:
                estado = "completo"

            resultado.append({
                "username": username,
                "fecha": fecha,
                "hora_entrada": horario["hora_entrada"] if horario else None,
                "hora_salida": horario["hora_salida"] if horario else None,
                "hora_entrada_real": entrada["hora_checkin"][:5] if entrada else None,
                "hora_salida_real": salida["hora_checkin"][:5] if salida else None,
                "retardo_min": retardo_min,
                "salida_anticipada_min": salida_anticipada_min,
                "horas_trabajadas": horas_trabajadas,
                "estado": estado,
                "hora_checkin": entrada["hora_checkin"][:5] if entrada else None,
            })

    return resultado
