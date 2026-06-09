from fastapi import APIRouter, Depends, HTTPException
from db import execute_read, execute_write
from auth import verify_token
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo
TZ = ZoneInfo("America/Tijuana")

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
def listar_unidades(current_user=Depends(verify_token)):
    return execute_read("SELECT * FROM unidades ORDER BY id_lote, unit_number")

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
