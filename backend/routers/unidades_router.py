from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.concurrency import run_in_threadpool
from db import execute_read, execute_write
from auth import verify_token
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo
import io
import zipfile
import asyncio
import logging
import base64
import json
import os
import requests

TZ = ZoneInfo("America/Tijuana")
logger = logging.getLogger(__name__)

# ── Importación opcional de OneDrive ────────────────────────────────────────
try:
    from onedrive_service import sync_zip_lote
    ONEDRIVE_ENABLED = True
except ImportError:
    ONEDRIVE_ENABLED = False

router = APIRouter(prefix="/api/unidades", tags=["unidades"])

CAMPOS_SERIES = [
    "vin_number","reefer_serial","reefer_model",
    "evaporator_serial_mjs11","evaporator_model_1",
    "evaporator_serial_mjd22","evaporator_model_2",
    "engine_serial","compressor_serial","generator_serial","battery_charger_serial"
]

# Modelos de evaporador disponibles para el desplegable (front y validación)
MODELOS_EVAPORADOR = ["", "MJD 1100", "MJS 1100", "MJD 2200", "MJS 2200", "N/A"]

class UnidadCreate(BaseModel):
    unit_number: str
    id_lote: str
    vin_number: Optional[str] = ""
    reefer_serial: Optional[str] = ""
    reefer_model: Optional[str] = ""
    evaporator_serial_mjs11: Optional[str] = ""
    evaporator_model_1: Optional[str] = ""
    evaporator_serial_mjd22: Optional[str] = ""
    evaporator_model_2: Optional[str] = ""
    engine_serial: Optional[str] = ""
    compressor_serial: Optional[str] = ""
    generator_serial: Optional[str] = ""
    battery_charger_serial: Optional[str] = ""

class SeriesUpdate(BaseModel):
    unit_number: str
    vin_number: Optional[str] = ""
    reefer_serial: Optional[str] = ""
    reefer_model: Optional[str] = ""
    evaporator_serial_mjs11: Optional[str] = ""
    evaporator_model_1: Optional[str] = ""
    evaporator_serial_mjd22: Optional[str] = ""
    evaporator_model_2: Optional[str] = ""
    engine_serial: Optional[str] = ""
    compressor_serial: Optional[str] = ""
    generator_serial: Optional[str] = ""
    battery_charger_serial: Optional[str] = ""

# ═══════════════════════════════════════════════════════════════════════════
# ── GESTIÓN DE LOTES — helper y endpoints (ANTES de /{unidad_id}) ──────────
# ═══════════════════════════════════════════════════════════════════════════

def _generar_zip_backup_lote(id_lote: str) -> bytes:
    """
    ZIP en memoria: CSV de series + todas las fotos de evidencia del lote.
    Usa una sola conexión DB con cursor propio para evitar 'Lost connection'
    en queries largas de blobs (evidencias).
    """
    import pymysql
    from db import get_db_connection

    conn = get_db_connection()
    if not conn:
        raise RuntimeError("No hay conexión con la base de datos")

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            # 1. Obtener unidades del lote
            cur.execute("SELECT * FROM unidades WHERE id_lote=%s ORDER BY unit_number", (id_lote,))
            unidades = cur.fetchall()
            if not unidades:
                return b""

            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
                # CSV con las series
                columnas = list(unidades[0].keys())
                lineas = [",".join(columnas)]
                for u in unidades:
                    lineas.append(",".join(str(u.get(c, "") or "") for c in columnas))
                zf.writestr(f"unidades_{id_lote}.csv", "\n".join(lineas))

                # Fotos de evidencia (meta primero, luego contenido en bloques)
                unit_numbers = [u["unit_number"] for u in unidades]
                if unit_numbers:
                    ph = ",".join(["%s"] * len(unit_numbers))
                    cur.execute(
                        f"SELECT id, unit_number, nombre_archivo FROM evidencias WHERE unit_number IN ({ph})",
                        tuple(unit_numbers)
                    )
                    meta = cur.fetchall()

                    if meta:
                        # Traer contenido de fotos en lotes de 50 para no saturar la conexión
                        LOTE_SIZE = 50
                        contenidos = {}
                        ids_lista = [m["id"] for m in meta]
                        for i in range(0, len(ids_lista), LOTE_SIZE):
                            bloque = ids_lista[i:i + LOTE_SIZE]
                            ph2 = ",".join(["%s"] * len(bloque))
                            cur.execute(
                                f"SELECT id, contenido FROM evidencias WHERE id IN ({ph2})",
                                tuple(bloque)
                            )
                            for fila in cur.fetchall():
                                if fila["contenido"]:
                                    contenidos[fila["id"]] = fila["contenido"]

                        nombres_vistos = {}
                        for m in meta:
                            contenido = contenidos.get(m["id"])
                            if not contenido:
                                continue
                            nombre = m["nombre_archivo"] or f"foto_{m['id']}.jpg"
                            key = (m["unit_number"], nombre)
                            if key in nombres_vistos:
                                nombres_vistos[key] += 1
                                partes = nombre.rsplit(".", 1)
                                nombre = (
                                    f"{partes[0]}_{nombres_vistos[key]}.{partes[1]}"
                                    if len(partes) == 2
                                    else f"{nombre}_{nombres_vistos[key]}"
                                )
                            else:
                                nombres_vistos[key] = 0
                            zf.writestr(f"evidencias/{m['unit_number']}/{nombre}", contenido)

            buf.seek(0)
            return buf.getvalue()
    finally:
        conn.close()


# GET /api/unidades/lotes  — listar lotes con conteo y estado oculto
@router.get("/lotes")
def listar_lotes(current_user=Depends(verify_token)):
    return execute_read("""
        SELECT id_lote,
               COUNT(*) AS total_unidades,
               MAX(oculto) AS oculto
        FROM unidades
        GROUP BY id_lote
        ORDER BY oculto ASC, id_lote ASC
    """)


# GET /api/unidades/lotes/backup?id_lote=XXX
@router.get("/lotes/backup")
async def descargar_backup_lote(
    id_lote: str = Query(..., description="ID del lote a respaldar"),
    current_user=Depends(verify_token)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    logger.info(f"[backup_lote] Solicitado backup para id_lote='{id_lote}'")

    existentes = execute_read("SELECT unit_number FROM unidades WHERE id_lote=%s", (id_lote,))
    if not existentes:
        todos = execute_read("SELECT DISTINCT id_lote FROM unidades")
        lotes_str = ", ".join(r["id_lote"] for r in todos) if todos else "(ninguno)"
        raise HTTPException(
            status_code=404,
            detail=f"Lote '{id_lote}' no encontrado. Disponibles: {lotes_str}"
        )

    zip_bytes = await run_in_threadpool(_generar_zip_backup_lote, id_lote)
    if not zip_bytes:
        raise HTTPException(status_code=500, detail="Error al generar el ZIP")

    nombre_safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in id_lote)
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=backup_lote_{nombre_safe}.zip",
            "Cache-Control": "no-store",
        }
    )


# POST /api/unidades/lotes/ocultar?id_lote=XXX&backup_onedrive=true/false
@router.post("/lotes/ocultar")
async def ocultar_lote(
    background_tasks: BackgroundTasks,
    id_lote: str = Query(...),
    backup_onedrive: bool = Query(False),
    current_user=Depends(verify_token)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")

    existentes = execute_read("SELECT id FROM unidades WHERE id_lote=%s", (id_lote,))
    if not existentes:
        raise HTTPException(status_code=404, detail=f"Lote '{id_lote}' no encontrado")

    # Ocultar el lote INMEDIATAMENTE — no esperar el backup
    execute_write("UPDATE unidades SET oculto=1 WHERE id_lote=%s", (id_lote,))

    respuesta = {
        "mensaje": f"Lote '{id_lote}' ocultado del dashboard",
        "unidades_afectadas": len(existentes),
    }

    if backup_onedrive:
        if not ONEDRIVE_ENABLED:
            respuesta["backup_aviso"] = "OneDrive no disponible en este servidor; el lote fue ocultado sin backup."
        else:
            # Lanzar backup en background — el cliente ya recibió confirmación
            def _tarea_backup():
                try:
                    logger.info(f"[ocultar_lote] Iniciando backup background para '{id_lote}'")
                    zip_bytes = _generar_zip_backup_lote(id_lote)
                    if zip_bytes:
                        web_url = sync_zip_lote(id_lote, zip_bytes)
                        logger.info(f"[ocultar_lote] Backup OneDrive completado: {web_url}")
                    else:
                        logger.warning(f"[ocultar_lote] ZIP vacío para '{id_lote}', sin backup")
                except Exception as e:
                    logger.error(f"[ocultar_lote] Backup OneDrive falló para '{id_lote}': {e}")

            background_tasks.add_task(_tarea_backup)
            respuesta["backup_aviso"] = "El backup a OneDrive se está procesando en segundo plano."

    return respuesta


# POST /api/unidades/lotes/mostrar?id_lote=XXX
@router.post("/lotes/mostrar")
def mostrar_lote(
    id_lote: str = Query(...),
    current_user=Depends(verify_token)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    existentes = execute_read("SELECT id FROM unidades WHERE id_lote=%s", (id_lote,))
    if not existentes:
        raise HTTPException(status_code=404, detail=f"Lote '{id_lote}' no encontrado")
    execute_write("UPDATE unidades SET oculto=0 WHERE id_lote=%s", (id_lote,))
    return {
        "mensaje": f"Lote '{id_lote}' visible nuevamente en el dashboard",
        "unidades_afectadas": len(existentes),
    }


# GET /api/unidades/lotes/auditar-carpetas-duplicadas
# Solo lectura: revisa OneDrive y reporta carpetas de evidencias duplicadas
# por unidad (causadas por el bug histórico de reefer_model mutable).
# No mueve ni borra nada — es insumo para decidir la fusión manual.
@router.get("/lotes/auditar-carpetas-duplicadas")
async def auditar_carpetas_duplicadas(
    id_lote: Optional[str] = Query(None, description="Si se omite, audita todos los lotes"),
    current_user=Depends(verify_token)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")

    from onedrive_service import auditar_carpetas_duplicadas_lote, auditar_todos_los_lotes

    try:
        if id_lote:
            resultado = await run_in_threadpool(auditar_carpetas_duplicadas_lote, id_lote)
            resultado["lotes_revisados"] = 1
            resultado["lotes_con_duplicados"] = 1 if resultado["duplicados"] else 0
            resultado["total_unidades_duplicadas"] = len(resultado["duplicados"])
            resultado["detalle"] = [resultado] if resultado["duplicados"] else []
        else:
            resultado = await run_in_threadpool(auditar_todos_los_lotes)
    except Exception as e:
        logger.error(f"[auditoria] Error auditando carpetas: {e}")
        raise HTTPException(status_code=502, detail=f"No se pudo auditar OneDrive: {e}")

    return resultado


# POST /api/unidades/lotes/fusionar-carpeta-duplicada
# Fusiona DOS carpetas de evidencias detectadas como duplicadas para la
# misma unidad: mueve el contenido de la carpeta pequeña/vieja (sin sufijo)
# dentro de la carpeta grande/nueva, renombra el resultado al patrón
# unit_number_reefer_serial, y borra la carpeta vieja ya vacía.
#
# Requiere los IDs de OneDrive de ambas carpetas (vienen del endpoint de
# auditoría) — esto evita adivinar o volver a buscar por nombre, y previene
# fusionar la carpeta equivocada por error de tipeo.
@router.post("/lotes/fusionar-carpeta-duplicada")
async def fusionar_carpeta_duplicada_endpoint(
    unit_number: str = Query(...),
    carpeta_chica_id: str = Query(..., description="ID de OneDrive de la carpeta con MENOS archivos"),
    carpeta_grande_id: str = Query(..., description="ID de OneDrive de la carpeta con MÁS archivos"),
    current_user=Depends(verify_token)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")

    filas = execute_read(
        "SELECT reefer_serial FROM unidades WHERE unit_number=%s LIMIT 1", (unit_number,)
    )
    if not filas:
        raise HTTPException(status_code=404, detail=f"Unidad '{unit_number}' no encontrada en BD")

    reefer_serial = (filas[0].get("reefer_serial") or "").strip()
    nombre_final = f"{unit_number}_{reefer_serial}" if reefer_serial else unit_number

    from onedrive_service import fusionar_carpeta_duplicada

    try:
        resultado = await run_in_threadpool(
            fusionar_carpeta_duplicada, carpeta_chica_id, carpeta_grande_id, nombre_final
        )
    except Exception as e:
        logger.error(f"[fusion] Error fusionando carpetas de '{unit_number}': {e}")
        raise HTTPException(status_code=502, detail=f"No se pudo fusionar en OneDrive: {e}")

    resultado["unit_number"] = unit_number
    return resultado


# GET /api/unidades/ficha?q=XXX
# "Ficha 360°" de una unidad: busca q en CUALQUIER identificador de serie
# (unit_number, VIN, reefer_serial, motor, compresor, generador, etc.) y
# devuelve TODA la información relacionada: datos completos de la unidad,
# actividades/asignaciones con su técnico y estado, comentarios de cada
# actividad, toma de valores registrados, tickets abiertos/cerrados,
# conteo de evidencias, y estado de lote (oculto/visible + backup OneDrive
# si existe).
#
# Esta ruta debe declararse ANTES de /{unidad_id} para que FastAPI no la
# confunda con un path param.
CAMPOS_SERIE_BUSCABLES = [
    "unit_number", "id_lote", "vin_number", "reefer_serial", "reefer_model",
    "evaporator_serial_mjs11", "evaporator_serial_mjd22",
    "engine_serial", "compressor_serial", "generator_serial",
    "battery_charger_serial",
]

@router.get("/ficha")
def ficha_unidad(q: str = Query(..., min_length=1), current_user=Depends(verify_token)):
    q = q.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Debes indicar un valor de búsqueda")

    # 1. Buscar la(s) unidad(es) por CUALQUIER campo de serie o el número de
    #    lote (coincidencia exacta primero; si no hay, se intenta parcial).
    #    Si el valor buscado corresponde a un lote con varias unidades,
    #    no se elige una al azar: se devuelve la lista completa para que
    #    el usuario seleccione cuál ficha quiere ver.
    condiciones = " OR ".join(f"{c}=%s" for c in CAMPOS_SERIE_BUSCABLES)
    params = [q] * len(CAMPOS_SERIE_BUSCABLES)
    filas = execute_read(
        f"SELECT * FROM unidades WHERE {condiciones} ORDER BY unit_number LIMIT 50",
        tuple(params)
    )

    if not filas:
        condiciones_like = " OR ".join(f"{c} LIKE %s" for c in CAMPOS_SERIE_BUSCABLES)
        params_like = [f"%{q}%"] * len(CAMPOS_SERIE_BUSCABLES)
        filas = execute_read(
            f"SELECT * FROM unidades WHERE {condiciones_like} ORDER BY unit_number LIMIT 50",
            tuple(params_like)
        )

    if not filas:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró ninguna unidad con '{q}' en VIN, series, lote o número económico"
        )

    if len(filas) > 1:
        return {
            "seleccion_multiple": True,
            "criterio": q,
            "unidades": [
                {
                    "unit_number": f["unit_number"],
                    "id_lote": f.get("id_lote"),
                    "vin_number": f.get("vin_number"),
                    "reefer_model": f.get("reefer_model"),
                }
                for f in filas
            ],
        }

    unidad = filas[0]
    unit_number = unidad["unit_number"]

    # 2. Asignaciones (actividades) de esta unidad — qué se ha hecho,
    #    quién lo hizo, en qué estado
    asignaciones = execute_read(
        "SELECT * FROM asignaciones WHERE unidad=%s ORDER BY id DESC", (unit_number,)
    )

    # 3. Comentarios de cada asignación de esta unidad
    asignacion_ids = [a["id"] for a in asignaciones]
    comentarios = []
    if asignacion_ids:
        placeholders = ",".join(["%s"] * len(asignacion_ids))
        comentarios = execute_read(
            f"SELECT * FROM comentarios_actividades WHERE asignacion_id IN ({placeholders}) "
            f"ORDER BY fecha DESC",
            tuple(asignacion_ids)
        )

    # 4. Toma de valores registrados en cualquiera de sus asignaciones
    toma_valores = []
    if asignacion_ids:
        placeholders = ",".join(["%s"] * len(asignacion_ids))
        toma_valores = execute_read(
            f"SELECT * FROM toma_valores_datos WHERE asignacion_id IN ({placeholders})",
            tuple(asignacion_ids)
        )

    # 5. Tickets de esta unidad
    tickets = execute_read(
        "SELECT * FROM tickets WHERE unit_number=%s ORDER BY id DESC", (unit_number,)
    )

    # 6. Evidencias — conteo total y lista de nombres (sin el contenido
    #    binario, para no inflar la respuesta)
    evidencias_count = execute_read(
        "SELECT COUNT(*) AS total FROM evidencias WHERE unit_number=%s", (unit_number,)
    )[0]["total"]
    evidencias_lista = execute_read(
        "SELECT id, nombre_archivo, tecnico, created_at FROM evidencias "
        "WHERE unit_number=%s ORDER BY created_at DESC LIMIT 200",
        (unit_number,)
    ) if evidencias_count else []

    # 7. Estado de lote: oculto/visible y si hay backup registrado en OneDrive
    lote_backup = None
    if unidad.get("id_lote"):
        rows_backup = execute_read(
            "SELECT * FROM lotes_backup_status WHERE id_lote=%s LIMIT 1",
            (unidad["id_lote"],)
        ) if _tabla_existe("lotes_backup_status") else []
        lote_backup = rows_backup[0] if rows_backup else None

    return {
        "unidad": unidad,
        "asignaciones": asignaciones,
        "comentarios": comentarios,
        "toma_valores": toma_valores,
        "tickets": tickets,
        "evidencias_total": evidencias_count,
        "evidencias": evidencias_lista,
        "lote_backup": lote_backup,
    }


def _tabla_existe(nombre_tabla: str) -> bool:
    """Verifica si una tabla existe en la BD, para no romper si aún no se ha creado."""
    try:
        execute_read(f"SELECT 1 FROM {nombre_tabla} LIMIT 1")
        return True
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════════════
# ── CRUD DE UNIDADES ────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════

# GET /api/unidades/
@router.get("/")
def listar_unidades(incluir_ocultas: bool = False, current_user=Depends(verify_token)):
    if incluir_ocultas:
        return execute_read("SELECT * FROM unidades ORDER BY id_lote, unit_number")
    return execute_read("SELECT * FROM unidades WHERE oculto=0 ORDER BY id_lote, unit_number")


# POST /api/unidades/
@router.post("/ocr-placa")
async def ocr_placa(file: UploadFile = File(...), current_user=Depends(verify_token)):
    """
    Analiza la foto de una placa de identificación (VIN, modelo, serie, etc.) usando IA
    y devuelve los campos que logre leer, para precargar el formulario de Registro de
    Unidades. El usuario siempre puede corregir/completar cualquier campo a mano.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="El escaneo de placas no está configurado en el servidor (falta ANTHROPIC_API_KEY)."
        )

    contenido = await file.read()
    if len(contenido) > 8 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="La imagen es demasiado grande (máx. 8MB).")

    media_type = file.content_type or "image/jpeg"
    b64 = base64.b64encode(contenido).decode("utf-8")

    prompt = (
        "Esta es una foto de la placa de identificación de una unidad de transporte "
        "refrigerado (trailer y/o equipo de refrigeración Carrier/Thermo King/Hyundai). "
        "Extrae ÚNICAMENTE los datos que veas escritos con claridad en la placa. "
        "Responde SOLO con un JSON válido (sin texto adicional, sin markdown, sin ```), "
        "con exactamente estas claves, usando cadena vacía \"\" cuando el dato no aparezca:\n"
        '{"vin_number": "", "reefer_model": "", "reefer_serial": "", "engine_serial": ""}\n\n'
        "vin_number = VIN / NIV completo. "
        "reefer_model = número de MODEL / MODELO de la placa. "
        "reefer_serial = SERIAL NO. o número de serie principal de la placa. "
        "engine_serial = solo si hay un número de serie de motor claramente separado; si no, deja vacío."
    )

    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": "claude-sonnet-4-6",
                "max_tokens": 500,
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                        {"type": "text", "text": prompt},
                    ],
                }],
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        texto = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        texto_limpio = texto.replace("```json", "").replace("```", "").strip()
        campos = json.loads(texto_limpio)
    except Exception as e:
        logger.error(f"Error en OCR de placa: {e}")
        raise HTTPException(
            status_code=502,
            detail="No se pudo leer la placa automáticamente. Intenta con otra foto o llena los campos a mano."
        )

    return {
        "vin_number": campos.get("vin_number", "") or "",
        "reefer_model": campos.get("reefer_model", "") or "",
        "reefer_serial": campos.get("reefer_serial", "") or "",
        "engine_serial": campos.get("engine_serial", "") or "",
    }


@router.post("/")
def crear_unidad(unidad: UnidadCreate, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    existente = execute_read("SELECT id FROM unidades WHERE unit_number=%s", (unidad.unit_number,))
    if existente:
        execute_write(
            """UPDATE unidades SET
               id_lote=%s, vin_number=%s, reefer_serial=%s, reefer_model=%s,
               evaporator_serial_mjs11=%s, evaporator_model_1=%s,
               evaporator_serial_mjd22=%s, evaporator_model_2=%s, engine_serial=%s,
               compressor_serial=%s, generator_serial=%s, battery_charger_serial=%s
               WHERE unit_number=%s""",
            (unidad.id_lote, unidad.vin_number, unidad.reefer_serial, unidad.reefer_model,
             unidad.evaporator_serial_mjs11, unidad.evaporator_model_1,
             unidad.evaporator_serial_mjd22, unidad.evaporator_model_2, unidad.engine_serial,
             unidad.compressor_serial, unidad.generator_serial, unidad.battery_charger_serial,
             unidad.unit_number)
        )
        return {"mensaje": "Unidad actualizada"}
    else:
        ahora = datetime.now(TZ).replace(tzinfo=None)
        execute_write(
            """INSERT INTO unidades
               (unit_number, id_lote, vin_number, reefer_serial, reefer_model,
                evaporator_serial_mjs11, evaporator_model_1,
                evaporator_serial_mjd22, evaporator_model_2, engine_serial,
                compressor_serial, generator_serial, battery_charger_serial, fecha_registro)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (unidad.unit_number, unidad.id_lote, unidad.vin_number, unidad.reefer_serial,
             unidad.reefer_model, unidad.evaporator_serial_mjs11, unidad.evaporator_model_1,
             unidad.evaporator_serial_mjd22, unidad.evaporator_model_2,
             unidad.engine_serial, unidad.compressor_serial, unidad.generator_serial,
             unidad.battery_charger_serial, ahora)
        )
        return {"mensaje": "Unidad registrada"}


# PUT /api/unidades/series/update  — ANTES de /{unidad_id} para evitar colisión
@router.put("/series/update")
def actualizar_series(data: SeriesUpdate, current_user=Depends(verify_token)):
    campos = {k: v for k, v in data.dict().items() if k != "unit_number" and v is not None}
    if not campos:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")
    set_parts = ", ".join([f"{k}=%s" for k in campos])
    values = list(campos.values()) + [data.unit_number]
    execute_write(f"UPDATE unidades SET {set_parts} WHERE unit_number=%s", values)
    return {"mensaje": "Series actualizadas"}


# PUT /api/unidades/{unidad_id}
@router.put("/{unidad_id}")
def editar_unidad(unidad_id: int, unidad: UnidadCreate, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")

    actual = execute_read("SELECT unit_number FROM unidades WHERE id=%s", (unidad_id,))
    if not actual:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")
    numero_anterior = actual[0]["unit_number"]

    execute_write(
        """UPDATE unidades SET
           unit_number=%s, id_lote=%s, vin_number=%s, reefer_serial=%s, reefer_model=%s,
           evaporator_serial_mjs11=%s, evaporator_model_1=%s,
           evaporator_serial_mjd22=%s, evaporator_model_2=%s, engine_serial=%s,
           compressor_serial=%s, generator_serial=%s, battery_charger_serial=%s
           WHERE id=%s""",
        (unidad.unit_number, unidad.id_lote, unidad.vin_number, unidad.reefer_serial,
         unidad.reefer_model, unidad.evaporator_serial_mjs11, unidad.evaporator_model_1,
         unidad.evaporator_serial_mjd22, unidad.evaporator_model_2,
         unidad.engine_serial, unidad.compressor_serial, unidad.generator_serial,
         unidad.battery_charger_serial, unidad_id)
    )

    # Si el número de unidad cambió, cascadear el nuevo número a todo lo que
    # ya se trabajó con el número anterior, para no perder el historial.
    if numero_anterior != unidad.unit_number:
        execute_write("UPDATE asignaciones SET unidad=%s WHERE unidad=%s",
                       (unidad.unit_number, numero_anterior))
        execute_write("UPDATE evidencias SET unit_number=%s WHERE unit_number=%s",
                       (unidad.unit_number, numero_anterior))
        try:
            execute_write("UPDATE tickets SET unit_number=%s WHERE unit_number=%s",
                           (unidad.unit_number, numero_anterior))
        except Exception:
            pass  # tabla tickets puede no existir en instalaciones antiguas

    return {"mensaje": "Unidad actualizada"}


@router.post("/homologar")
def homologar_unidad(numero_anterior: str, numero_correcto: str, current_user=Depends(verify_token)):
    """
    Reasigna TODO el historial (asignaciones, evidencias, tickets) que haya quedado
    ligado a `numero_anterior` (p.ej. un número mal capturado) hacia `numero_correcto`.
    Úsalo cuando ya se registró una unidad duplicada por error de captura y quedaron
    dos números para la misma unidad física.
    """
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    if numero_anterior == numero_correcto:
        raise HTTPException(status_code=400, detail="Los números deben ser diferentes")

    destino = execute_read("SELECT id FROM unidades WHERE unit_number=%s", (numero_correcto,))
    if not destino:
        raise HTTPException(status_code=404, detail=f"No existe una unidad con el número {numero_correcto}")

    asig = execute_write("UPDATE asignaciones SET unidad=%s WHERE unidad=%s",
                          (numero_correcto, numero_anterior))
    evid = execute_write("UPDATE evidencias SET unit_number=%s WHERE unit_number=%s",
                          (numero_correcto, numero_anterior))
    tick = 0
    try:
        tick = execute_write("UPDATE tickets SET unit_number=%s WHERE unit_number=%s",
                              (numero_correcto, numero_anterior))
    except Exception:
        pass

    # Si además quedó un registro duplicado en `unidades` con el número viejo, lo eliminamos
    origen = execute_read("SELECT id FROM unidades WHERE unit_number=%s", (numero_anterior,))
    eliminado = False
    if origen:
        execute_write("DELETE FROM unidades WHERE unit_number=%s", (numero_anterior,))
        eliminado = True

    return {
        "mensaje": f"Historial de '{numero_anterior}' reasignado a '{numero_correcto}'",
        "asignaciones_migradas": asig,
        "evidencias_migradas": evid,
        "tickets_migrados": tick,
        "unidad_duplicada_eliminada": eliminado
    }


# DELETE /api/unidades/{unidad_id}
@router.delete("/{unidad_id}")
def eliminar_unidad(unidad_id: int, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    unidad = execute_read("SELECT unit_number FROM unidades WHERE id=%s", (unidad_id,))
    if not unidad:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")
    unit_number = unidad[0]["unit_number"]
    execute_write("DELETE FROM evidencias WHERE unit_number=%s", (unit_number,))
    execute_write("DELETE FROM asignaciones WHERE unidad=%s", (unit_number,))
    execute_write("DELETE FROM unidades WHERE id=%s", (unidad_id,))
    return {"mensaje": "Unidad y sus datos relacionados eliminados"}
