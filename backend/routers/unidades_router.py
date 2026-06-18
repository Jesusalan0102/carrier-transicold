from fastapi import APIRouter, Depends, HTTPException
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

# ── LISTAR ─────────────────────────────────────────────────────────────────
@router.get("/")
def listar_unidades(incluir_ocultas: bool = False, current_user=Depends(verify_token)):
    if incluir_ocultas:
        return execute_read("SELECT * FROM unidades ORDER BY id_lote, unit_number")
    return execute_read(
        "SELECT * FROM unidades WHERE oculto=0 ORDER BY id_lote, unit_number"
    )

# ── CREAR / ACTUALIZAR (upsert) ────────────────────────────────────────────
@router.post("/")
def crear_unidad(unidad: UnidadCreate, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")

    # Verificar si la unidad ya existe
    existente = execute_read(
        "SELECT id FROM unidades WHERE unit_number=%s", (unidad.unit_number,)
    )

    if existente:
        # Ya existe → actualizar datos SIN tocar fecha_registro
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
        # Nueva unidad → registrar con fecha_registro = ahora (hora Tijuana)
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

# ── EDITAR COMPLETA (admin panel) ──────────────────────────────────────────
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

# ── ACTUALIZAR SERIES (técnico desde Toma de Series) ──────────────────────
@router.put("/series/update")
def actualizar_series(data: SeriesUpdate, current_user=Depends(verify_token)):
    campos = {k: v for k, v in data.dict().items() if k != "unit_number" and v is not None}
    if not campos:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")
    set_parts = ", ".join([f"{k}=%s" for k in campos])
    values = list(campos.values()) + [data.unit_number]
    execute_write(f"UPDATE unidades SET {set_parts} WHERE unit_number=%s", values)
    return {"mensaje": "Series actualizadas"}

# ── ELIMINAR (admin) ───────────────────────────────────────────────────────
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


# ═════════════════════════════════════════════════════════════════════════
# ── GESTIÓN DE VISIBILIDAD DE LOTES (ocultar / mostrar) ────────────────────
# ═════════════════════════════════════════════════════════════════════════

def _generar_zip_backup_lote(id_lote: str) -> bytes:
    """
    Construye un ZIP en memoria con:
      - unidades_<lote>.csv  (series de todas las unidades del lote)
      - evidencias/<unit_number>/<archivo>  (todas las fotos de evidencia)
    """
    unidades = execute_read(
        "SELECT * FROM unidades WHERE id_lote=%s ORDER BY unit_number", (id_lote,)
    )
    if not unidades:
        return b""

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
        # ── CSV con las series de las unidades ────────────────────────────
        columnas = [c for c in unidades[0].keys()]
        lineas = [",".join(columnas)]
        for u in unidades:
            lineas.append(",".join(str(u.get(c, "") or "") for c in columnas))
        zf.writestr(f"unidades_{id_lote}.csv", "\n".join(lineas))

        # ── Evidencias de cada unidad del lote ─────────────────────────────
        unit_numbers = [u["unit_number"] for u in unidades]
        if unit_numbers:
            placeholders = ",".join(["%s"] * len(unit_numbers))
            meta = execute_read(
                f"SELECT id, unit_number, nombre_archivo FROM evidencias WHERE unit_number IN ({placeholders})",
                tuple(unit_numbers)
            )
            if meta:
                ids = tuple(m["id"] for m in meta)
                ph2 = ",".join(["%s"] * len(ids))
                filas = execute_read(
                    f"SELECT id, contenido FROM evidencias WHERE id IN ({ph2})", ids
                )
                contenidos = {f["id"]: f["contenido"] for f in filas if f["contenido"]}
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


# ── LISTAR LOTES (con conteo de unidades y estado oculto) ─────────────────
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


# ── DESCARGAR BACKUP ZIP DE UN LOTE (sin ocultar) ──────────────────────────
@router.get("/lotes/{id_lote:path}/backup")
async def descargar_backup_lote(id_lote: str, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    logger.info(f"[backup_lote] Solicitado backup para id_lote='{id_lote}'")
    # Verificar que el lote existe antes de generar el ZIP
    existentes = execute_read(
        "SELECT unit_number FROM unidades WHERE id_lote=%s", (id_lote,)
    )
    logger.info(f"[backup_lote] Unidades encontradas: {len(existentes) if existentes else 0}")
    if not existentes:
        # Mostrar lotes disponibles para debug
        todos = execute_read("SELECT DISTINCT id_lote FROM unidades")
        lotes_str = ", ".join(r["id_lote"] for r in todos) if todos else "(ninguno)"
        logger.warning(f"[backup_lote] Lote '{id_lote}' no encontrado. Lotes en DB: {lotes_str}")
        raise HTTPException(status_code=404, detail=f"Lote '{id_lote}' no encontrado. Lotes disponibles: {lotes_str}")
    zip_bytes = await run_in_threadpool(_generar_zip_backup_lote, id_lote)
    if not zip_bytes:
        raise HTTPException(status_code=500, detail="Error al generar el ZIP")
    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=backup_lote_{id_lote}.zip",
            "Cache-Control": "no-store",
        }
    )


# ── OCULTAR LOTE (con backup opcional a OneDrive) ──────────────────────────
@router.post("/lotes/{id_lote:path}/ocultar")
async def ocultar_lote(
    id_lote: str,
    backup_onedrive: bool = False,
    current_user=Depends(verify_token)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")

    existentes = execute_read(
        "SELECT id FROM unidades WHERE id_lote=%s", (id_lote,)
    )
    if not existentes:
        raise HTTPException(status_code=404, detail="Lote no encontrado")

    web_url = None
    if backup_onedrive:
        if not ONEDRIVE_ENABLED:
            raise HTTPException(
                status_code=503,
                detail="Integración con OneDrive no disponible en este servidor"
            )
        zip_bytes = await run_in_threadpool(_generar_zip_backup_lote, id_lote)
        if zip_bytes:
            try:
                web_url = await run_in_threadpool(sync_zip_lote, id_lote, zip_bytes)
            except Exception as e:
                logger.error(f"[ocultar_lote] Backup a OneDrive falló para '{id_lote}': {e}")
                raise HTTPException(
                    status_code=502,
                    detail=f"No se pudo subir el backup a OneDrive: {e}"
                )

    execute_write("UPDATE unidades SET oculto=1 WHERE id_lote=%s", (id_lote,))

    respuesta = {
        "mensaje": f"Lote '{id_lote}' ocultado del dashboard",
        "unidades_afectadas": len(existentes),
    }
    if web_url:
        respuesta["backup_onedrive_url"] = web_url
    return respuesta


# ── MOSTRAR LOTE (revertir ocultamiento) ───────────────────────────────────
@router.post("/lotes/{id_lote:path}/mostrar")
def mostrar_lote(id_lote: str, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    existentes = execute_read(
        "SELECT id FROM unidades WHERE id_lote=%s", (id_lote,)
    )
    if not existentes:
        raise HTTPException(status_code=404, detail="Lote no encontrado")
    execute_write("UPDATE unidades SET oculto=0 WHERE id_lote=%s", (id_lote,))
    return {
        "mensaje": f"Lote '{id_lote}' visible nuevamente en el dashboard",
        "unidades_afectadas": len(existentes),
    }
