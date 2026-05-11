from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth import verify_token
from db import execute_read, execute_write
from typing import Dict

router = APIRouter(prefix="/api/toma-valores", tags=["toma_valores"])

class ValoresGuardar(BaseModel):
    asignacion_id: int
    valores: Dict[str, str]

class CampoCreate(BaseModel):
    campo_nombre: str

# ── CAMPOS ─────────────────────────────────────────────────────────────────
@router.get("/campos")
def get_campos(current_user=Depends(verify_token)):
    return execute_read("SELECT campo_nombre, campo_orden FROM toma_valores_campos ORDER BY campo_orden")

@router.post("/campos")
def agregar_campo(data: CampoCreate, current_user=Depends(verify_token)):
    existe = execute_read(
        "SELECT id FROM toma_valores_campos WHERE campo_nombre=%s", (data.campo_nombre,)
    )
    if existe:
        raise HTTPException(status_code=400, detail="El campo ya existe")
    max_orden = execute_read("SELECT MAX(campo_orden) as max_o FROM toma_valores_campos")
    orden = 0 if not max_orden or max_orden[0]["max_o"] is None else max_orden[0]["max_o"] + 1
    execute_write(
        "INSERT INTO toma_valores_campos (campo_nombre, campo_orden) VALUES (%s,%s)",
        (data.campo_nombre, orden)
    )
    return {"mensaje": f"Campo '{data.campo_nombre}' agregado"}

@router.delete("/campos/{nombre}")
def eliminar_campo(nombre: str, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    execute_write("DELETE FROM toma_valores_campos WHERE campo_nombre=%s", (nombre,))
    return {"mensaje": f"Campo '{nombre}' eliminado"}

# ── DATOS POR ASIGNACIÓN ───────────────────────────────────────────────────
@router.get("/datos/{asignacion_id}")
def get_datos(asignacion_id: int, current_user=Depends(verify_token)):
    rows = execute_read(
        "SELECT campo_nombre, valor FROM toma_valores_datos WHERE asignacion_id=%s",
        (asignacion_id,)
    )
    return {r["campo_nombre"]: r["valor"] or "" for r in rows}

@router.post("/guardar")
def guardar_valores(data: ValoresGuardar, current_user=Depends(verify_token)):
    execute_write("DELETE FROM toma_valores_datos WHERE asignacion_id=%s", (data.asignacion_id,))
    for campo, valor in data.valores.items():
        execute_write(
            "INSERT INTO toma_valores_datos (asignacion_id, campo_nombre, valor) VALUES (%s,%s,%s)",
            (data.asignacion_id, campo, valor)
        )
    return {"mensaje": "Valores guardados"}
