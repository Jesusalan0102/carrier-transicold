from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
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
    "evaporator_serial_mjs11","evaporator_serial_mjd22",
    "engine_serial","compressor_serial","generator_serial","battery_charger_serial"
]

class UnidadCreate(BaseModel):
    unit_number: str
    id_lote: str
    vin_number: Optional[str] = ""
    reefer_serial: Optional[str] = ""
    reefer_model: Optional[str] = ""
    evaporator_serial_mjs11: Optional[str] = ""
    evaporator_serial_mjd22: Optional[str] = ""
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
    evaporator_serial_mjd22: Optional[str] = ""
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
@router.post("/")
def crear_unidad(unidad: UnidadCreate, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    existente = execute_read("SELECT id FROM unidades WHERE unit_number=%s", (unidad.unit_number,))
    if existente:
        execute_write(
            """UPDATE unidades SET
               id_lote=%s, vin_number=%s, reefer_serial=%s, reefer_model=%s,
               evaporator_serial_mjs11=%s, evaporator_serial_mjd22=%s, engine_serial=%s,
               compressor_serial=%s, generator_serial=%s, battery_charger_serial=%s
               WHERE unit_number=%s""",
            (unidad.id_lote, unidad.vin_number, unidad.reefer_serial, unidad.reefer_model,
             unidad.evaporator_serial_mjs11, unidad.evaporator_serial_mjd22, unidad.engine_serial,
             unidad.compressor_serial, unidad.generator_serial, unidad.battery_charger_serial,
             unidad.unit_number)
        )
        return {"mensaje": "Unidad actualizada"}
    else:
        ahora = datetime.now(TZ).replace(tzinfo=None)
        execute_write(
            """INSERT INTO unidades
               (unit_number, id_lote, vin_number, reefer_serial, reefer_model,
                evaporator_serial_mjs11, evaporator_serial_mjd22, engine_serial,
                compressor_serial, generator_serial, battery_charger_serial, fecha_registro)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (unidad.unit_number, unidad.id_lote, unidad.vin_number, unidad.reefer_serial,
             unidad.reefer_model, unidad.evaporator_serial_mjs11, unidad.evaporator_serial_mjd22,
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
    execute_write(
        """UPDATE unidades SET
           unit_number=%s, id_lote=%s, vin_number=%s, reefer_serial=%s, reefer_model=%s,
           evaporator_serial_mjs11=%s, evaporator_serial_mjd22=%s, engine_serial=%s,
           compressor_serial=%s, generator_serial=%s, battery_charger_serial=%s
           WHERE id=%s""",
        (unidad.unit_number, unidad.id_lote, unidad.vin_number, unidad.reefer_serial,
         unidad.reefer_model, unidad.evaporator_serial_mjs11, unidad.evaporator_serial_mjd22,
         unidad.engine_serial, unidad.compressor_serial, unidad.generator_serial,
         unidad.battery_charger_serial, unidad_id)
    )
    return {"mensaje": "Unidad actualizada"}


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
