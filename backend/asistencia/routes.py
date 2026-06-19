"""
asistencia/routes.py — Backend de Asistencia Carrier Transicold

Fixes aplicados:
  - /inasistencias: nuevo endpoint que devuelve técnicos ausentes en un rango
    de fechas, cruzando horarios vs registros_asistencia
  - /importar-horarios: endpoint para importar horarios desde CSV/JSON
  - /registros: ahora filtra con DATE() para evitar desfases de timezone
  - Retardo se calcula siempre desde el horario guardado en DB, no desde
    una hora hardcodeada
"""

from fastapi import APIRouter, HTTPException, Query, Depends, UploadFile, File
from pydantic import BaseModel
from typing import Optional, List
import pymysql
from db import get_db_connection, execute_read, execute_write
from datetime import datetime, date, timedelta
import zoneinfo
import os
import base64
import csv
import io
from auth import verify_token
from asistencia.asistencia.gps_validator import validar_ubicacion, es_gps_preciso

TZ_TJ = zoneinfo.ZoneInfo("America/Tijuana")

router = APIRouter(prefix="/asistencia", tags=["Asistencia"])

GPS_ACCURACY_LIMIT = 50


# ── Schemas ────────────────────────────────────────────────────────────────────

class GeofenceConfig(BaseModel):
    lat_fija: float
    lon_fija: float
    radio_metros: int


class RegistroAsistenciaBody(BaseModel):
    tipo: str
    lat: Optional[float] = None
    lon: Optional[float] = None
    accuracy: Optional[float] = None
    foto_base64: Optional[str] = None


class HorarioImportItem(BaseModel):
    username: str
    fecha: str          # "YYYY-MM-DD"
    hora_entrada: Optional[str] = None   # "HH:MM"
    hora_salida:  Optional[str] = None   # "HH:MM"


class HorariosImportBatch(BaseModel):
    registros: List[HorarioImportItem]


# ── Helper ────────────────────────────────────────────────────────────────────

def _to_str(val) -> Optional[str]:
    if val is None:
        return None
    if hasattr(val, "isoformat"):
        return val.isoformat()
    if hasattr(val, "seconds"):          # timedelta (TIME de pymysql)
        total = val.seconds
        h = total // 3600
        m = (total % 3600) // 60
        return f"{h:02d}:{m:02d}"
    return str(val)


def _semana_de_fecha(fecha_str: str) -> str:
    """Devuelve el lunes (YYYY-MM-DD) de la semana que contiene fecha_str."""
    d = date.fromisoformat(fecha_str)
    lunes = d - timedelta(days=d.weekday())
    return lunes.isoformat()


# ── GET /api/asistencia/registros ─────────────────────────────────────────────

@router.get("/registros")
def obtener_registros(fecha: str = Query(None)):
    connection = get_db_connection()
    if not connection:
        raise HTTPException(500, "No hay conexión con la base de datos")
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            if fecha:
                # FIX: DATE() explícito para evitar desfases de timezone
                cursor.execute(
                    """
                    SELECT username, DATE_FORMAT(fecha,'%%Y-%%m-%%d') AS fecha,
                           tipo, hora_checkin, latitud, longitud,
                           distancia_metros, aprobado, retardo_min
                    FROM registros_asistencia
                    WHERE DATE(fecha) = %s
                    ORDER BY hora_checkin
                    """,
                    (fecha,)
                )
            else:
                cursor.execute(
                    """
                    SELECT username, DATE_FORMAT(fecha,'%%Y-%%m-%%d') AS fecha,
                           tipo, hora_checkin, latitud, longitud,
                           distancia_metros, aprobado, retardo_min
                    FROM registros_asistencia
                    ORDER BY fecha DESC, hora_checkin DESC
                    LIMIT 500
                    """
                )
            registros = cursor.fetchall()
            result = []
            for r in registros:
                row = dict(r)
                if row.get("hora_checkin"):
                    row["hora_checkin"] = str(row["hora_checkin"])[:8]
                result.append(row)
            return result
    except Exception as e:
        print(f"[registros] Error: {e}")
        raise HTTPException(500, str(e))
    finally:
        connection.close()



# Debug
@router.get("/debug-registros")
def debug_registros(current_user=Depends(verify_token)):
    if current_user.get("role") != "admin":
        raise HTTPException(403, "Solo administradores")
    connection = get_db_connection()
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM registros_asistencia")
            total = cursor.fetchone()["total"]
            cursor.execute("SELECT * FROM registros_asistencia ORDER BY fecha DESC, hora_checkin DESC LIMIT 50")
            rows = cursor.fetchall()
            return {"total_registros": total, "ultimos_50": rows}
    finally:
        connection.close()


# ── GET /api/asistencia/inasistencias ─────────────────────────────────────────
# Nuevo endpoint: devuelve lista de técnicos ausentes en un rango de fechas.
# Un técnico es "ausente" cuando tiene horario programado pero NO tiene
# ningún registro de entrada en registros_asistencia para esa fecha.

@router.get("/inasistencias")
def obtener_inasistencias(
    fecha_inicio: str = Query(...),
    fecha_fin:    str = Query(None),
    current_user=Depends(verify_token)
):
    if current_user["role"] not in ("admin", "visor"):
        raise HTTPException(403, "Solo administradores o visores")

    if not fecha_fin:
        fecha_fin = fecha_inicio

    try:
        inicio = date.fromisoformat(fecha_inicio)
        fin    = date.fromisoformat(fecha_fin)
    except ValueError:
        raise HTTPException(400, "Fechas inválidas (esperado YYYY-MM-DD)")

    # Generar lista de fechas del rango
    fechas = []
    d = inicio
    while d <= fin:
        fechas.append(d.isoformat())
        d += timedelta(days=1)

    if not fechas:
        return []

    placeholders = ",".join(["%s"] * len(fechas))

    # Horarios programados en el rango
    horarios_raw = execute_read(
        f"SELECT username, DATE_FORMAT(fecha,'%%Y-%%m-%%d') AS fecha, "
        f"hora_entrada, hora_salida FROM horarios WHERE fecha IN ({placeholders})",
        tuple(fechas)
    ) or []

    # Registros reales (solo entradas) en el rango
    registros_raw = execute_read(
        f"""
        SELECT username, DATE_FORMAT(fecha,'%%Y-%%m-%%d') AS fecha
        FROM registros_asistencia
        WHERE tipo='entrada' AND DATE(fecha) IN ({placeholders})
        """,
        tuple(fechas)
    ) or []

    # Conjunto de (username, fecha) que SÍ checarón entrada
    checaron = {(r["username"], str(r["fecha"])) for r in registros_raw}

    inasistencias = []
    for h in horarios_raw:
        f = str(h["fecha"])
        # Solo cuentan los días con horario asignado (no días libres)
        tiene_horario = h.get("hora_entrada") or h.get("hora_salida")
        if not tiene_horario:
            continue
        if (h["username"], f) not in checaron:
            inasistencias.append({
                "username":     h["username"],
                "fecha":        f,
                "dia_semana":   date.fromisoformat(f).strftime("%A"),
                "hora_entrada": _to_str(h["hora_entrada"]),
                "hora_salida":  _to_str(h["hora_salida"]),
            })

    # Ordenar por fecha y username
    inasistencias.sort(key=lambda x: (x["fecha"], x["username"]))
    return inasistencias


# ── POST /api/asistencia/importar-horarios ────────────────────────────────────
# Importa horarios desde JSON (batch) o CSV (archivo).
# JSON: { "registros": [{ "username", "fecha", "hora_entrada", "hora_salida" }] }
# CSV:  columnas: username, fecha, hora_entrada, hora_salida

@router.post("/importar-horarios")
async def importar_horarios(
    payload: Optional[HorariosImportBatch] = None,
    archivo: Optional[UploadFile] = File(None),
    current_user=Depends(verify_token)
):
    if current_user["role"] != "admin":
        raise HTTPException(403, "Solo administradores")

    registros: List[HorarioImportItem] = []

    # Fuente 1: JSON directo
    if payload and payload.registros:
        registros = payload.registros

    # Fuente 2: CSV subido
    elif archivo:
        contenido = await archivo.read()
        texto = contenido.decode("utf-8-sig")   # maneja BOM de Excel
        reader = csv.DictReader(io.StringIO(texto))
        for fila in reader:
            username     = (fila.get("username") or "").strip()
            fecha        = (fila.get("fecha") or "").strip()
            hora_entrada = (fila.get("hora_entrada") or "").strip() or None
            hora_salida  = (fila.get("hora_salida") or "").strip() or None
            if not username or not fecha:
                continue
            registros.append(HorarioImportItem(
                username=username,
                fecha=fecha,
                hora_entrada=hora_entrada,
                hora_salida=hora_salida,
            ))
    else:
        raise HTTPException(400, "Envía JSON con 'registros' o un archivo CSV")

    if not registros:
        return {"ok": True, "guardados": 0, "eliminados": 0, "errores": []}

    guardados  = 0
    eliminados = 0
    errores    = []

    for item in registros:
        try:
            # Calcular semana (lunes)
            semana = _semana_de_fecha(item.fecha)
        except Exception:
            errores.append(f"{item.username} / {item.fecha}: fecha inválida")
            continue

        entrada = (item.hora_entrada or "").strip()
        salida  = (item.hora_salida  or "").strip()

        existente = execute_read(
            "SELECT id FROM horarios WHERE username=%s AND fecha=%s",
            (item.username, item.fecha)
        )

        try:
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
                        (entrada or None, salida or None, semana,
                         item.username, item.fecha)
                    )
                else:
                    execute_write(
                        "INSERT INTO horarios (username, fecha, semana, hora_entrada, hora_salida) "
                        "VALUES (%s,%s,%s,%s,%s)",
                        (item.username, item.fecha, semana,
                         entrada or None, salida or None)
                    )
                guardados += 1
        except Exception as e:
            errores.append(f"{item.username} / {item.fecha}: {e}")

    return {
        "ok":        True,
        "guardados": guardados,
        "eliminados": eliminados,
        "errores":   errores,
    }


# ── GET /api/asistencia/configuracion ────────────────────────────────────────

@router.get("/configuracion")
def obtener_configuracion():
    connection = get_db_connection()
    if not connection:
        raise HTTPException(500, "No hay conexión con la base de datos")
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(
                "SELECT lat_fija, lon_fija, radio_metros FROM configuracion_geocerca LIMIT 1"
            )
            config = cursor.fetchone()
            if not config:
                return {"lat_fija": 32.471823, "lon_fija": -116.798104, "radio_metros": 200}
            return config
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        connection.close()


@router.post("/configuracion")
def guardar_configuracion(config: GeofenceConfig):
    connection = get_db_connection()
    if not connection:
        raise HTTPException(500, "No hay conexión con la base de datos")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM configuracion_geocerca")
            res = cursor.fetchone()
            count = res.get("count", 0) if isinstance(res, dict) else res[0]
            if count > 0:
                cursor.execute(
                    "UPDATE configuracion_geocerca SET lat_fija=%s, lon_fija=%s, radio_metros=%s",
                    (config.lat_fija, config.lon_fija, config.radio_metros)
                )
            else:
                cursor.execute(
                    "INSERT INTO configuracion_geocerca (lat_fija, lon_fija, radio_metros) "
                    "VALUES (%s,%s,%s)",
                    (config.lat_fija, config.lon_fija, config.radio_metros)
                )
            connection.commit()
            return {"status": "success", "message": "Geocerca actualizada"}
    except Exception as e:
        connection.rollback()
        raise HTTPException(500, str(e))
    finally:
        connection.close()


# ── POST /api/asistencia/registrar ───────────────────────────────────────────

@router.post("/registrar")
async def registrar_asistencia(
    body: RegistroAsistenciaBody,
    current_user=Depends(verify_token)
):
    username = current_user["username"]
    tipo = body.tipo

    if tipo not in ("entrada", "salida"):
        raise HTTPException(400, "Tipo debe ser 'entrada' o 'salida'")

    # 1. Validar precisión GPS — MODO SOLO-REGISTRO: nunca se rechaza el check-in.
    #    Se conserva el dato de precisión/ubicación para auditoría, pero ya no
    #    bloquea a nadie. (Antes: HTTPException 422 si accuracy > GPS_ACCURACY_LIMIT)
    gps_ok, gps_msg = es_gps_preciso(body.accuracy, limite_metros=GPS_ACCURACY_LIMIT)

    # 2. Validar geocerca — MODO SOLO-REGISTRO: si no hay coordenadas (permiso
    #    de ubicación denegado), simplemente se registra sin dato de distancia.
    config = obtener_configuracion()
    if body.lat is None or body.lon is None:
        dentro, distancia = True, None
    else:
        dentro, distancia, _ = validar_ubicacion(
            lat_tecnico=body.lat, lon_tecnico=body.lon,
            lat_fija=config["lat_fija"], lon_fija=config["lon_fija"],
            radio_metros=config["radio_metros"]
        )
    aprobado = 1 if dentro else 0

    # 3. Hora Tijuana
    now_tj    = datetime.now(TZ_TJ)
    fecha_hoy = now_tj.date().isoformat()
    hora_actual = now_tj.strftime("%H:%M:%S")

    # 4. Foto base64
    foto_bytes = None
    if body.foto_base64:
        try:
            foto_bytes = base64.b64decode(body.foto_base64.split(",", 1)[-1])
        except Exception:
            foto_bytes = None

    # 5. Calcular retardo (solo entradas)
    retardo_min = 0
    if tipo == "entrada":
        try:
            horario_rows = execute_read(
                "SELECT hora_entrada FROM horarios WHERE username=%s AND fecha=%s LIMIT 1",
                (username, fecha_hoy)
            )
            if horario_rows and horario_rows[0].get("hora_entrada"):
                he = horario_rows[0]["hora_entrada"]
                he_str = _to_str(he)
                prog_min = int(he_str[:2]) * 60 + int(he_str[3:5])
                real_min = int(hora_actual[:2]) * 60 + int(hora_actual[3:5])
                retardo_min = max(0, real_min - prog_min - 15)
        except Exception as e:
            print(f"[retardo] {e}")
            retardo_min = 0

    # 6. Insertar en DB
    distancia_redondeada = round(distancia) if distancia is not None else None
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO registros_asistencia
                  (username, fecha, tipo, hora_checkin, latitud, longitud,
                   distancia_metros, aprobado, retardo_min, foto)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (username, fecha_hoy, tipo, hora_actual,
                 body.lat, body.lon, distancia_redondeada,
                 aprobado, retardo_min, foto_bytes)
            )
            connection.commit()

        return {
            "ok":               True,
            "aprobado":         bool(aprobado),
            "distancia_metros": distancia_redondeada,
            "radio_metros":     config["radio_metros"],
            "accuracy_metros":  body.accuracy,
            "gps_sin_dato":     body.lat is None or body.lon is None,
            "hora":             hora_actual,
            "fecha":            fecha_hoy,
            "tipo":             tipo,
            "retardo_min":      retardo_min,
            "mensaje": "✅ Registro exitoso" + (
                " (sin dato de ubicación)" if body.lat is None or body.lon is None else ""
            )
        }
    except Exception as e:
        print(f"[registrar] {e}")
        raise HTTPException(500, str(e))
    finally:
        connection.close()


# ── GET /api/asistencia/generar-qr ───────────────────────────────────────────

@router.get("/generar-qr")
def generar_qr():
    connection = get_db_connection()
    if not connection:
        raise HTTPException(500, "No hay conexión con la base de datos")
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(
                "SELECT lat_fija, lon_fija, radio_metros FROM configuracion_geocerca LIMIT 1"
            )
            config = cursor.fetchone() or {
                "lat_fija": 32.471823, "lon_fija": -116.798104, "radio_metros": 200
            }
        base_url = os.getenv("APP_BASE_URL", "").rstrip("/")
        return {"qr_url": f"{base_url}/app/checkin", "config": config}
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        connection.close()
