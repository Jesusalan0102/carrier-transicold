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

from fastapi import APIRouter, Depends, Query, HTTPException, UploadFile, File
from pydantic import BaseModel

from auth import verify_token
from db import execute_read, execute_write

import io
import unicodedata

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


# ── POST /api/horarios/importar-excel ──────────────────────────────────────────
# Parsea un .xlsx con columnas: Técnico (username), Nombre Completo,
# Lunes Entrada, Lunes Salida, ..., Sábado Entrada, Sábado Salida
# Hace fuzzy matching de nombre → username si la columna username está vacía.
# Devuelve un preview JSON para que el admin confirme antes de guardar.

def _normalizar(s: str) -> str:
    """Lowercase, sin tildes, sin espacios extra."""
    s = s.strip().lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return " ".join(s.split())


def _similitud(a: str, b: str) -> float:
    """Ratio de palabras en común (0-1)."""
    wa = set(_normalizar(a).split())
    wb = set(_normalizar(b).split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / max(len(wa), len(wb))


DIAS_COLS = [
    ("Lunes",     "lunes_entrada",     "lunes_salida"),
    ("Martes",    "martes_entrada",    "martes_salida"),
    ("Miércoles", "miercoles_entrada", "miercoles_salida"),
    ("Jueves",    "jueves_entrada",    "jueves_salida"),
    ("Viernes",   "viernes_entrada",   "viernes_salida"),
    ("Sábado",    "sabado_entrada",    "sabado_salida"),
]


def _parse_hora(val) -> Optional[str]:
    """Convierte cualquier representación de hora a HH:MM o None."""
    if val is None:
        return None
    s = str(val).strip()
    if not s or s in ("-", ""):
        return None
    # Formato HH:MM:SS o HH:MM
    parts = s.split(":")
    if len(parts) >= 2:
        try:
            h = int(parts[0])
            m = int(parts[1])
            return f"{h:02d}:{m:02d}"
        except Exception:
            pass
    return None


@router.post("/importar-excel")
async def importar_excel(
    semana: str = Query(..., description="YYYY-MM-DD (lunes de la semana)"),
    file: UploadFile = File(...),
    current_user=Depends(verify_token)
):
    """
    Recibe un .xlsx, lo parsea y devuelve un preview con el matching
    username → nombre_completo para que el admin confirme.
    """
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")

    # Validar semana
    try:
        lunes = date.fromisoformat(semana)
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de semana inválido (YYYY-MM-DD)")

    # Calcular fechas de la semana
    fechas_semana = [(lunes + timedelta(days=i)).isoformat() for i in range(6)]

    # Leer archivo
    content = await file.read()
    try:
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"No se pudo leer el archivo Excel: {e}")

    # Buscar hoja "Horarios" (o la primera)
    hoja_nombre = "Horarios" if "Horarios" in wb.sheetnames else wb.sheetnames[0]
    ws = wb[hoja_nombre]

    # Leer encabezados de la primera fila
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        raise HTTPException(status_code=400, detail="El archivo está vacío")

    headers = [str(h).strip() if h is not None else "" for h in rows[0]]

    # Mapear columnas por nombre
    def col_idx(name: str) -> Optional[int]:
        name_n = _normalizar(name)
        for i, h in enumerate(headers):
            if _normalizar(h) == name_n:
                return i
        return None

    idx_username = col_idx("Técnico (username)")
    idx_nombre   = col_idx("Nombre Completo")

    col_map = {}
    for dia_label, key_e, key_s in DIAS_COLS:
        col_map[key_e] = col_idx(f"{dia_label} Entrada")
        col_map[key_s] = col_idx(f"{dia_label} Salida")

    if idx_nombre is None:
        raise HTTPException(status_code=400, detail="No se encontró la columna 'Nombre Completo'")

    # Cargar técnicos de la BD para hacer matching
    users_db = execute_read(
        "SELECT username, COALESCE(nombre_completo, username) AS nombre FROM users WHERE role='tecnico'"
    ) or []

    # Intentar con nombre_completo; si la columna no existe, usar username
    try:
        users_db2 = execute_read(
            "SELECT username, nombre_completo AS nombre FROM users WHERE role='tecnico' AND nombre_completo IS NOT NULL"
        ) or []
        if users_db2:
            users_db = users_db2
    except Exception:
        pass

    def buscar_username(nombre_excel: str) -> Optional[str]:
        mejor = None
        mejor_score = 0.0
        for u in users_db:
            score = _similitud(nombre_excel, u["nombre"])
            if score > mejor_score:
                mejor_score = score
                mejor = u["username"]
        return mejor if mejor_score >= 0.5 else None

    # Parsear filas de datos
    preview_rows = []
    sin_match = []

    for row in rows[1:]:
        nombre = row[idx_nombre] if idx_nombre is not None else None
        if not nombre:
            continue
        nombre = str(nombre).strip()
        if not nombre:
            continue

        # Username: primero del Excel, luego fuzzy match
        username_excel = None
        if idx_username is not None:
            v = row[idx_username]
            if v:
                username_excel = str(v).strip() or None

        username_matched = username_excel or buscar_username(nombre)
        confianza = "manual" if username_excel else ("auto" if username_matched else "sin_match")

        horarios_dia = []
        for i, (dia_label, key_e, key_s) in enumerate(DIAS_COLS):
            entrada = _parse_hora(row[col_map[key_e]] if col_map.get(key_e) is not None else None)
            salida  = _parse_hora(row[col_map[key_s]] if col_map.get(key_s) is not None else None)
            horarios_dia.append({
                "fecha":        fechas_semana[i],
                "dia":          dia_label,
                "hora_entrada": entrada,
                "hora_salida":  salida,
            })

        entry = {
            "nombre_excel":     nombre,
            "username":         username_matched,
            "confianza":        confianza,
            "horarios":         horarios_dia,
        }
        preview_rows.append(entry)
        if not username_matched:
            sin_match.append(nombre)

    # Lista de técnicos disponibles para el selector de corrección manual
    tecnicos_disponibles = [u["username"] for u in (execute_read(
        "SELECT username FROM users WHERE role='tecnico' ORDER BY username"
    ) or [])]

    return {
        "semana":               semana,
        "fechas_semana":        fechas_semana,
        "preview":              preview_rows,
        "sin_match":            sin_match,
        "tecnicos_disponibles": tecnicos_disponibles,
        "total":                len(preview_rows),
    }


# ── POST /api/horarios/confirmar-importacion ────────────────────────────────────
# Recibe el preview (ya con usernames corregidos) y los guarda en la BD.

class HorarioImportDia(BaseModel):
    fecha:        str
    hora_entrada: Optional[str] = None
    hora_salida:  Optional[str] = None

class HorarioImportRow(BaseModel):
    username: str
    horarios: List[HorarioImportDia]

class ConfirmarImportacion(BaseModel):
    semana:   str
    registros: List[HorarioImportRow]

@router.post("/confirmar-importacion")
def confirmar_importacion(payload: ConfirmarImportacion, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")

    guardados  = 0
    eliminados = 0

    for row in payload.registros:
        if not row.username:
            continue
        for dia in row.horarios:
            entrada = (dia.hora_entrada or "").strip()
            salida  = (dia.hora_salida  or "").strip()

            existente = execute_read(
                "SELECT id FROM horarios WHERE username=%s AND fecha=%s",
                (row.username, dia.fecha)
            )

            if not entrada and not salida:
                if existente:
                    execute_write(
                        "DELETE FROM horarios WHERE username=%s AND fecha=%s",
                        (row.username, dia.fecha)
                    )
                    eliminados += 1
            else:
                if existente:
                    execute_write(
                        "UPDATE horarios SET hora_entrada=%s, hora_salida=%s, semana=%s "
                        "WHERE username=%s AND fecha=%s",
                        (entrada or None, salida or None, payload.semana,
                         row.username, dia.fecha)
                    )
                else:
                    execute_write(
                        "INSERT INTO horarios (username, fecha, semana, hora_entrada, hora_salida) "
                        "VALUES (%s,%s,%s,%s,%s)",
                        (row.username, dia.fecha, payload.semana,
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
