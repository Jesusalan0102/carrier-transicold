from fastapi import APIRouter, Depends, HTTPException
from db import execute_read, execute_write, execute_write_with_id
from auth import verify_token
from pydantic import BaseModel
from typing import Optional, Dict
import json

router = APIRouter(prefix="/api/schedule", tags=["schedule"])


def _row_to_dict(r: dict) -> dict:
    dias = r.get("dias")
    if isinstance(dias, str):
        try:
            dias = json.loads(dias) if dias else {}
        except Exception:
            dias = {}
    r["dias"] = dias or {}
    return r


class ScheduleFila(BaseModel):
    mes_anio: str
    linea: Optional[str] = ""
    owner: Optional[str] = ""
    size: Optional[str] = ""
    tipo: Optional[str] = ""
    reefer_brand: Optional[str] = ""
    notas_evaps: Optional[str] = ""
    qty: Optional[int] = 0
    model_no: Optional[str] = ""
    dias: Optional[Dict[str, int]] = {}


class ReordenItem(BaseModel):
    id: int
    orden: int


class ReordenPayload(BaseModel):
    items: list[ReordenItem]


# ── MESES DISPONIBLES ─────────────────────────────────────────────────────
@router.get("/meses")
def listar_meses(current_user=Depends(verify_token)):
    rows = execute_read(
        "SELECT DISTINCT mes_anio FROM schedule_produccion ORDER BY mes_anio DESC"
    )
    return [r["mes_anio"] for r in rows]


# ── FILAS DE UN MES ───────────────────────────────────────────────────────
@router.get("/")
def listar_filas(mes_anio: str, current_user=Depends(verify_token)):
    rows = execute_read(
        "SELECT * FROM schedule_produccion WHERE mes_anio=%s ORDER BY orden ASC, id ASC",
        (mes_anio,)
    )
    return [_row_to_dict(dict(r)) for r in rows]


@router.post("/")
def crear_fila(data: ScheduleFila, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    max_orden = execute_read(
        "SELECT MAX(orden) as m FROM schedule_produccion WHERE mes_anio=%s", (data.mes_anio,)
    )
    next_orden = 0 if not max_orden or max_orden[0]["m"] is None else max_orden[0]["m"] + 1
    new_id = execute_write_with_id(
        """INSERT INTO schedule_produccion
           (mes_anio, orden, linea, owner, size, tipo, reefer_brand, notas_evaps, qty, model_no, dias)
           VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
        (data.mes_anio, next_orden, data.linea, data.owner, data.size, data.tipo,
         data.reefer_brand, data.notas_evaps, data.qty, data.model_no,
         json.dumps(data.dias or {}))
    )
    return {"mensaje": "Fila creada", "id": new_id, "orden": next_orden}


@router.put("/{fila_id}")
def actualizar_fila(fila_id: int, data: ScheduleFila, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    afectados = execute_write(
        """UPDATE schedule_produccion
           SET linea=%s, owner=%s, size=%s, tipo=%s, reefer_brand=%s,
               notas_evaps=%s, qty=%s, model_no=%s, dias=%s
           WHERE id=%s""",
        (data.linea, data.owner, data.size, data.tipo, data.reefer_brand,
         data.notas_evaps, data.qty, data.model_no, json.dumps(data.dias or {}), fila_id)
    )
    if not afectados:
        raise HTTPException(status_code=404, detail="Fila no encontrada")
    return {"mensaje": "Fila actualizada"}


@router.delete("/{fila_id}")
def eliminar_fila(fila_id: int, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    execute_write("DELETE FROM schedule_produccion WHERE id=%s", (fila_id,))
    return {"mensaje": "Fila eliminada"}


@router.put("/reordenar/lote")
def reordenar_filas(payload: ReordenPayload, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    for item in payload.items:
        execute_write("UPDATE schedule_produccion SET orden=%s WHERE id=%s", (item.orden, item.id))
    return {"mensaje": "Orden actualizado"}
