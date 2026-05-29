"""
horarios_routes.py — Rutas de horarios semanales
Maneja:
  - GET  /api/horarios/           → Horarios de la semana
  - POST /api/horarios/           → Guarda horarios (batch)
  - GET  /api/horarios/hoy        → Horario de un técnico en una fecha concreta
  - GET  /api/horarios/resumen    → Resumen de asistencia cruzado con horarios
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Ajusta los imports según tu estructura real:
from database import get_db
from models import Horario, AsistenciaRegistro

router = APIRouter(prefix="/api/horarios", tags=["horarios"])


# ═══════════════════════════════════════════════════════════════════════════════
# SCHEMAS
# ═══════════════════════════════════════════════════════════════════════════════

class HorarioItem(BaseModel):
    username:      str
    fecha:         str    # "YYYY-MM-DD"
    semana:        str    # "YYYY-MM-DD" (lunes de esa semana)
    hora_entrada:  Optional[str] = None   # "HH:MM" | ""
    hora_salida:   Optional[str] = None   # "HH:MM" | ""

class HorariosBatch(BaseModel):
    registros: List[HorarioItem]


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/horarios/ — Horarios de la semana
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/")
async def get_horarios(semana: Optional[str] = Query(None), db: Session = Depends(get_db)):
    """
    Devuelve todos los horarios de una semana dada.
    Parámetro semana: "YYYY-MM-DD" (lunes).
    """
    query = db.query(Horario)
    if semana:
        query = query.filter(Horario.semana == semana)
    horarios = query.all()
    return [
        {
            "id":           h.id,
            "username":     h.username,
            "fecha":        h.fecha,
            "semana":       h.semana,
            "hora_entrada": h.hora_entrada,
            "hora_salida":  h.hora_salida,
        }
        for h in horarios
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# POST /api/horarios/ — Guardar horarios (upsert batch)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/")
async def save_horarios(payload: HorariosBatch, db: Session = Depends(get_db)):
    """
    Guarda o actualiza (upsert) los horarios de una semana.
    Registros con hora_entrada y hora_salida vacíos se eliminan (día libre).
    """
    guardados = 0
    eliminados = 0

    for item in payload.registros:
        entrada = (item.hora_entrada or "").strip()
        salida  = (item.hora_salida  or "").strip()

        existente = (
            db.query(Horario)
            .filter(Horario.username == item.username, Horario.fecha == item.fecha)
            .first()
        )

        if not entrada and not salida:
            # Día libre — borrar si existía
            if existente:
                db.delete(existente)
                eliminados += 1
        else:
            if existente:
                existente.hora_entrada = entrada or None
                existente.hora_salida  = salida  or None
                existente.semana       = item.semana
            else:
                nuevo = Horario(
                    username     = item.username,
                    fecha        = item.fecha,
                    semana       = item.semana,
                    hora_entrada = entrada or None,
                    hora_salida  = salida  or None,
                )
                db.add(nuevo)
            guardados += 1

    db.commit()
    return {"ok": True, "guardados": guardados, "eliminados": eliminados}


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/horarios/hoy — Horario de un técnico en una fecha
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/hoy")
async def get_horario_hoy(
    username: str = Query(...),
    fecha:    str = Query(...),
    db: Session = Depends(get_db),
):
    """
    Devuelve el horario de un técnico para una fecha específica.
    Si no existe, devuelve horario: null (sin horario ese día).

    Respuesta:
    {
        "horario": {
            "hora_entrada": "08:00" | null,
            "hora_salida":  "17:00" | null
        } | null
    }
    """
    horario = (
        db.query(Horario)
        .filter(Horario.username == username, Horario.fecha == fecha)
        .first()
    )

    if not horario:
        return {"horario": None}

    return {
        "horario": {
            "hora_entrada": horario.hora_entrada,
            "hora_salida":  horario.hora_salida,
        }
    }


# ═══════════════════════════════════════════════════════════════════════════════
# GET /api/horarios/resumen — Resumen semanal cruzado con asistencia real
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/resumen")
async def get_resumen(semana: str = Query(...), db: Session = Depends(get_db)):
    """
    Cruza los horarios de la semana con los registros de asistencia reales.
    Devuelve por técnico y fecha:
      - hora_entrada / hora_salida programadas
      - hora_entrada_real / hora_salida_real (registradas)
      - retardo_min de entrada
      - salida_anticipada_min (si salió antes)
      - horas_trabajadas
      - estado: 'completo' | 'sin_salida' | 'sin_entrada' | 'ausente' | 'libre'

    Respuesta: lista de objetos con los campos anteriores.
    """
    # Calcular fechas de la semana (lunes a sábado)
    from datetime import date, timedelta
    try:
        lunes = date.fromisoformat(semana)
    except ValueError:
        return []

    fechas = [(lunes + timedelta(days=i)).isoformat() for i in range(6)]

    # Horarios programados de la semana
    horarios = (
        db.query(Horario)
        .filter(Horario.semana == semana)
        .all()
    )
    horarios_map = {(h.username, h.fecha): h for h in horarios}

    # Registros reales de la semana
    registros = (
        db.query(AsistenciaRegistro)
        .filter(AsistenciaRegistro.fecha.in_(fechas))
        .all()
    )

    # Indexar por (username, fecha, tipo)
    reg_map = {}
    for r in registros:
        key = (r.username, r.fecha, r.tipo)
        reg_map[key] = r

    # Técnicos que aparecen en horarios O en registros
    tecnicos = set(h.username for h in horarios) | set(r.username for r in registros)

    resultado = []
    for username in sorted(tecnicos):
        for fecha in fechas:
            horario  = horarios_map.get((username, fecha))
            entrada  = reg_map.get((username, fecha, "entrada"))
            salida   = reg_map.get((username, fecha, "salida"))

            # Sin horario y sin registro → omitir
            if not horario and not entrada and not salida:
                continue

            def hhmm_min(hhmm):
                if not hhmm: return None
                try:
                    h, m = hhmm[:5].split(":")
                    return int(h) * 60 + int(m)
                except:
                    return None

            e_prog  = hhmm_min(horario.hora_entrada[:5] if horario and horario.hora_entrada else None)
            s_prog  = hhmm_min(horario.hora_salida[:5]  if horario and horario.hora_salida  else None)
            e_real  = hhmm_min(entrada.hora_checkin[:5] if entrada else None)
            s_real  = hhmm_min(salida.hora_checkin[:5]  if salida  else None)

            # Retardo de entrada (tolerancia 15 min)
            retardo_min = 0
            if e_prog is not None and e_real is not None:
                retardo_min = max(0, e_real - e_prog - 15)

            # Salida anticipada
            salida_anticipada_min = 0
            if s_prog is not None and s_real is not None:
                salida_anticipada_min = max(0, s_prog - s_real)

            # Horas trabajadas
            horas_trabajadas = None
            if e_real is not None and s_real is not None:
                total = max(0, s_real - e_real)
                horas_trabajadas = round(total / 60, 2)

            # Estado
            if not horario or (not horario.hora_entrada and not horario.hora_salida):
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
                "username":             username,
                "fecha":                fecha,
                "hora_entrada":         horario.hora_entrada if horario else None,
                "hora_salida":          horario.hora_salida  if horario else None,
                "hora_entrada_real":    entrada.hora_checkin[:5] if entrada else None,
                "hora_salida_real":     salida.hora_checkin[:5]  if salida  else None,
                "retardo_min":          retardo_min,
                "salida_anticipada_min": salida_anticipada_min,
                "horas_trabajadas":     horas_trabajadas,
                "estado":               estado,
                # Compat. retrocompatibilidad con el resumen anterior
                "hora_checkin":         entrada.hora_checkin[:5] if entrada else None,
            })

    return resultado
