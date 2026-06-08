"""
horarios_routes.py — Rutas de horarios semanales
Fixes aplicados:
  - /resumen: query unificada que cruza horarios + registros_asistencia
    correctamente por username Y fecha (sin desfase de timezone)
  - Inasistencias: técnicos con horario pero SIN ningún registro ahora
    aparecen como "ausente" en vez de desaparecer del resumen
  - Retardos: se recalculan aquí también para que el resumen sea
    consistente con lo que guarda routes.py al momento del check-in
  - /mios: ahora devuelve registros REALES de check-in (no horarios programados)
    para que el historial del técnico muestre sus entradas/salidas reales
"""

from datetime import date, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel

from auth import verify_token
from db import execute_read, execute_write

import zoneinfo
from datetime import datetime

TZ_TJ = zoneinfo.ZoneInfo("America/Tijuana")


def ahora_tijuana():
    return datetime.now(TZ_TJ)


router = APIRouter(prefix="/api/horarios", tags=["horarios"])


# ── Schemas ────────────────────────────────────────────────────────────────────

class HorarioItem(BaseModel):
    username: str
    fecha: str        # "YYYY-MM-DD"
    semana: str       # "YYYY-MM-DD" (lunes de esa semana)
    hora_entrada: Optional[str] = None   # "HH:MM"
    hora_salida:  Optional[str] = None   # "HH:MM"


class HorariosBatch(BaseModel):
    registros: List[HorarioItem]


# ── Helpers ────────────────────────────────────────────────────────────────────

def _to_str(val) -> Optional[str]:
    """Convierte fecha/timedelta/string a string limpio."""
    if val is None:
        return None
    if hasattr(val, "isoformat"):   # date / datetime
        return val.isoformat()
    if hasattr(val, "seconds"):     # timedelta (TIME de pymysql)
        total = val.seconds
        h = total // 3600
        m = (total % 3600) // 60
        return f"{h:02d}:{m:02d}"
    return str(val)


def _hhmm_to_min(hhmm: Optional[str]) -> Optional[int]:
    if not hhmm:
        return None
    try:
        parts = str(hhmm)[:5].split(":")
        return int(parts[0]) * 60 + int(parts[1])
    except Exception:
        return None


# ── GET /api/horarios/ ─────────────────────────────────────────────────────────

@router.get("/")
def get_horarios(
    semana: Optional[str] = Query(None),
    current_user=Depends(verify_token)
):
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
            "id":           r["id"],
            "username":     r["username"],
            "fecha":        _to_str(r["fecha"]),
            "semana":       _to_str(r["semana"]),
            "hora_entrada": _to_str(r["hora_entrada"]),
            "hora_salida":  _to_str(r["hora_salida"]),
        }
        for r in (rows or [])
    ]


# ── GET /api/horarios/mios ─────────────────────────────────────────────────────
# FIX: ahora devuelve registros REALES de check-in, no horarios programados.
# Así el técnico ve sus entradas/salidas reales en el historial.

@router.get("/mios")
def get_mis_horarios(
    semana: Optional[str] = Query(None),
    current_user=Depends(verify_token)
):
    username = current_user["username"]

    if semana:
        # Calcular fechas de la semana
        try:
            lunes = date.fromisoformat(semana)
        except ValueError:
            raise HTTPException(400, "Formato de semana inválido (esperado YYYY-MM-DD)")
        fechas = [(lunes + timedelta(days=i)).isoformat() for i in range(6)]
        placeholders = ",".join(["%s"] * len(fechas))

        # Horarios programados de la semana
        horarios_rows = execute_read(
            f"SELECT fecha, hora_entrada, hora_salida FROM horarios "
            f"WHERE username=%s AND fecha IN ({placeholders})",
            (username, *fechas)
        ) or []

        # Registros reales de check-in de la semana
        registros_rows = execute_read(
            f"SELECT fecha, tipo, hora_checkin FROM registros_asistencia "
            f"WHERE username=%s AND fecha IN ({placeholders}) "
            f"ORDER BY hora_checkin",
            (username, *fechas)
        ) or []

    else:
        # Últimos 14 días
        horarios_rows = execute_read(
            "SELECT fecha, hora_entrada, hora_salida FROM horarios "
            "WHERE username=%s ORDER BY fecha DESC LIMIT 14",
            (username,)
        ) or []

        registros_rows = execute_read(
            "SELECT fecha, tipo, hora_checkin FROM registros_asistencia "
            "WHERE username=%s ORDER BY fecha DESC, hora_checkin DESC LIMIT 28",
            (username,)
        ) or []

    # Cruzar: para cada fecha, devolver hora programada + hora real
    horarios_map = {}
    for h in horarios_rows:
        f = _to_str(h["fecha"])
        horarios_map[f] = {
            "hora_entrada": _to_str(h["hora_entrada"]),
            "hora_salida":  _to_str(h["hora_salida"]),
        }

    registros_map: dict = {}
    for r in registros_rows:
        f = _to_str(r["fecha"])
        if f not in registros_map:
            registros_map[f] = {"entrada": None, "salida": None}
        tipo = r["tipo"]
        hora = _to_str(r["hora_checkin"])
        if hora and len(hora) >= 5:
            hora = hora[:5]
        if tipo == "entrada" and not registros_map[f]["entrada"]:
            registros_map[f]["entrada"] = hora
        elif tipo == "salida":
            registros_map[f]["salida"] = hora

    # Unión de fechas de ambas fuentes
    todas_fechas = sorted(set(list(horarios_map.keys()) + list(registros_map.keys())), reverse=True)

    resultado = []
    for f in todas_fechas[:14]:
        prog = horarios_map.get(f, {})
        real = registros_map.get(f, {})
        resultado.append({
            "fecha":             f,
            "hora_entrada":      prog.get("hora_entrada"),   # programada
            "hora_salida":       prog.get("hora_salida"),    # programada
            "entrada_real":      real.get("entrada"),        # check-in real
            "salida_real":       real.get("salida"),         # check-out real
        })

    return resultado


# ── POST /api/horarios/ ────────────────────────────────────────────────────────

@router.post("/")
def save_horarios(payload: HorariosBatch, current_user=Depends(verify_token)):
    if current_user["role"] not in ("admin",):
        raise HTTPException(status_code=403, detail="Solo administradores")

    guardados  = 0
    eliminados = 0

    for item in payload.registros:
        entrada = (item.hora_entrada or "").strip()
        salida  = (item.hora_salida  or "").strip()

        existente = execute_read(
            "SELECT id FROM horarios WHERE username=%s AND fecha=%s",
            (item.username, item.fecha)
        )

        if not entrada and not salida:
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
    fecha: str    = Query(...),
    current_user=Depends(verify_token)
):
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
            "hora_entrada": _to_str(h["hora_entrada"]),
            "hora_salida":  _to_str(h["hora_salida"]),
        }
    }


# ── GET /api/horarios/resumen ──────────────────────────────────────────────────
# FIX PRINCIPAL: query unificada que garantiza que técnicos con horario
# pero sin check-in aparezcan como "ausente", y que el cruce de datos
# use DATE() explícito para evitar desfases de timezone.

@router.get("/resumen")
def get_resumen(
    semana: str = Query(...),
    current_user=Depends(verify_token)
):
    if current_user["role"] not in ("admin", "visor"):
        raise HTTPException(status_code=403, detail="Solo administradores o visores")

    try:
        lunes = date.fromisoformat(semana)
    except ValueError:
        return []

    fechas = [(lunes + timedelta(days=i)).isoformat() for i in range(6)]
    placeholders = ",".join(["%s"] * len(fechas))

    # ── Horarios programados ──────────────────────────────────────────────────
    horarios_raw = execute_read(
        "SELECT username, fecha, hora_entrada, hora_salida "
        "FROM horarios WHERE semana=%s",
        (semana,)
    ) or []

    horarios_map: dict = {}
    for h in horarios_raw:
        f = _to_str(h["fecha"])
        horarios_map[(h["username"], f)] = {
            "hora_entrada": _to_str(h["hora_entrada"]),
            "hora_salida":  _to_str(h["hora_salida"]),
        }

    # ── Registros reales de check-in ──────────────────────────────────────────
    # FIX: usamos DATE(fecha) para evitar que diferencias de timezone rompan
    # el filtro, y traemos todos los campos necesarios en una sola query.
    registros_raw = execute_read(
        f"""
        SELECT username,
               DATE_FORMAT(fecha, '%%Y-%%m-%%d') AS fecha,
               tipo,
               hora_checkin,
               distancia_metros,
               aprobado,
               retardo_min
        FROM registros_asistencia
        WHERE DATE(fecha) IN ({placeholders})
        ORDER BY hora_checkin
        """,
        tuple(fechas)
    ) or []

    # reg_map[(username, fecha, tipo)] = registro
    # Si hay duplicados de tipo (dos entradas el mismo día), queda la primera.
    reg_map: dict = {}
    for r in registros_raw:
        f = str(r["fecha"])
        key = (r["username"], f, r["tipo"])
        if key not in reg_map:
            reg_map[key] = r

    # ── Técnicos: unión de los que tienen horario + los que checan aunque sea ──
    tecnicos = (
        {h["username"] for h in horarios_raw}
        | {r["username"] for r in registros_raw}
    )

    resultado = []
    for username in sorted(tecnicos):
        for fecha in fechas:
            horario = horarios_map.get((username, fecha))
            entrada = reg_map.get((username, fecha, "entrada"))
            salida  = reg_map.get((username, fecha, "salida"))

            # Si no hay horario programado ni registro, omitir la fila
            if not horario and not entrada and not salida:
                continue

            # Horas programadas en minutos
            he_prog = _hhmm_to_min(horario["hora_entrada"] if horario else None)
            hs_prog = _hhmm_to_min(horario["hora_salida"]  if horario else None)

            # Horas reales (hora_checkin puede ser timedelta de pymysql TIME)
            he_str = _to_str(entrada["hora_checkin"])[:5] if entrada and entrada.get("hora_checkin") else None
            hs_str = _to_str(salida["hora_checkin"])[:5]  if salida  and salida.get("hora_checkin")  else None

            he_real = _hhmm_to_min(he_str)
            hs_real = _hhmm_to_min(hs_str)

            # Retardo: preferir el valor ya calculado al momento del check-in,
            # recalcular solo si falta (migración de registros viejos).
            if entrada and entrada.get("retardo_min") is not None:
                retardo_min = int(entrada["retardo_min"])
            elif he_prog is not None and he_real is not None:
                TOLERANCIA = 15
                retardo_min = max(0, he_real - he_prog - TOLERANCIA)
            else:
                retardo_min = 0

            salida_anticipada_min = (
                max(0, hs_prog - hs_real)
                if hs_prog is not None and hs_real is not None
                else 0
            )

            horas_trabajadas = (
                round(max(0, hs_real - he_real) / 60, 2)
                if he_real is not None and hs_real is not None
                else None
            )

            # ── Estado ───────────────────────────────────────────────────────
            tiene_horario = horario and (
                horario.get("hora_entrada") or horario.get("hora_salida")
            )

            if not tiene_horario:
                estado = "libre"
            elif not entrada and not salida:
                estado = "ausente"          # ← inasistencia detectada aquí
            elif entrada and not salida:
                estado = "sin_salida"
            elif not entrada and salida:
                estado = "sin_entrada"
            else:
                estado = "completo"

            resultado.append({
                "username":             username,
                "fecha":                fecha,
                # Programado
                "hora_entrada":         horario["hora_entrada"] if horario else None,
                "hora_salida":          horario["hora_salida"]  if horario else None,
                # Real (check-in)
                "hora_entrada_real":    he_str,
                "hora_salida_real":     hs_str,
                "hora_checkin":         he_str,   # alias para compatibilidad con frontend
                # Métricas
                "retardo_min":          retardo_min,
                "salida_anticipada_min": salida_anticipada_min,
                "horas_trabajadas":     horas_trabajadas,
                # Estado
                "estado":               estado,
                # Extra para el admin
                "distancia_metros":     entrada.get("distancia_metros") if entrada else None,
                "aprobado":             bool(entrada.get("aprobado")) if entrada else None,
            })

    return resultado
