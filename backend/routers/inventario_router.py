from fastapi import APIRouter, Depends, HTTPException
from db import execute_read, execute_write
from auth import verify_token
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/inventario", tags=["inventario"])

class RenombrarColumna(BaseModel):
    nombre_actual: str
    nombre_nuevo: str

# ── COLUMNAS ───────────────────────────────────────────────────────────────
@router.get("/columnas")
def get_columnas(current_user=Depends(verify_token)):
    rows = execute_read(
        "SELECT col_nombre FROM inventario_columnas WHERE tabla_nombre='Principal' ORDER BY col_orden ASC"
    )
    if rows:
        return [r["col_nombre"] for r in rows]
    # Columnas por defecto si no hay ninguna
    defaults = ["Código","Descripción","Cantidad","Unidad","Ubicación","Estado"]
    for i, c in enumerate(defaults):
        execute_write(
            "INSERT INTO inventario_columnas (tabla_nombre, col_nombre, col_orden) VALUES (%s,%s,%s)",
            ("Principal", c, i)
        )
    return defaults

@router.post("/columnas")
def save_columnas(columnas: List[str], current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    execute_write("DELETE FROM inventario_columnas WHERE tabla_nombre='Principal'")
    for i, c in enumerate(columnas):
        execute_write(
            "INSERT INTO inventario_columnas (tabla_nombre, col_nombre, col_orden) VALUES (%s,%s,%s)",
            ("Principal", c, i)
        )
    return {"mensaje": "Columnas guardadas"}

@router.put("/columnas/renombrar")
def renombrar_columna(data: RenombrarColumna, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    execute_write(
        "UPDATE inventario_columnas SET col_nombre=%s WHERE col_nombre=%s AND tabla_nombre='Principal'",
        (data.nombre_nuevo, data.nombre_actual)
    )
    execute_write(
        "UPDATE inventario_data SET col_nombre=%s WHERE col_nombre=%s AND tabla_nombre='Principal'",
        (data.nombre_nuevo, data.nombre_actual)
    )
    return {"mensaje": f"Columna renombrada a '{data.nombre_nuevo}'"}

@router.delete("/columnas/{nombre}")
def eliminar_columna(nombre: str, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    execute_write(
        "DELETE FROM inventario_columnas WHERE col_nombre=%s AND tabla_nombre='Principal'", (nombre,)
    )
    execute_write(
        "DELETE FROM inventario_data WHERE col_nombre=%s AND tabla_nombre='Principal'", (nombre,)
    )
    return {"mensaje": f"Columna '{nombre}' eliminada"}

# ── DATOS ──────────────────────────────────────────────────────────────────
@router.get("/datos")
def get_datos(current_user=Depends(verify_token)):
    columnas = get_columnas(current_user)
    rows = execute_read(
        "SELECT fila_idx, col_nombre, valor FROM inventario_data WHERE tabla_nombre='Principal' ORDER BY fila_idx, col_nombre"
    )
    data_dict = {}
    for r in rows:
        fi = r["fila_idx"]
        if fi not in data_dict:
            data_dict[fi] = {c: "" for c in columnas}
        if r["col_nombre"] in columnas:
            data_dict[fi][r["col_nombre"]] = r["valor"] or ""
    return [data_dict[k] for k in sorted(data_dict.keys())]

@router.post("/datos")
def save_datos(datos: List[dict], current_user=Depends(verify_token)):
    execute_write("DELETE FROM inventario_data WHERE tabla_nombre='Principal'")
    for i, row in enumerate(datos):
        for col, val in row.items():
            execute_write(
                "INSERT INTO inventario_data (tabla_nombre, fila_idx, col_nombre, valor) VALUES (%s,%s,%s,%s)",
                ("Principal", i, col, str(val))
            )
    return {"mensaje": "Datos guardados"}

@router.post("/datos/fila")
def agregar_fila(current_user=Depends(verify_token)):
    columnas = get_columnas(current_user)
    max_idx = execute_read("SELECT MAX(fila_idx) as max_idx FROM inventario_data WHERE tabla_nombre='Principal'")
    next_idx = 0 if not max_idx or max_idx[0]["max_idx"] is None else max_idx[0]["max_idx"] + 1
    for col in columnas:
        execute_write(
            "INSERT INTO inventario_data (tabla_nombre, fila_idx, col_nombre, valor) VALUES (%s,%s,%s,%s)",
            ("Principal", next_idx, col, "")
        )
    return {"mensaje": "Fila agregada", "fila_idx": next_idx}

@router.delete("/datos/fila/{fila_idx}")
def eliminar_fila(fila_idx: int, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    execute_write(
        "DELETE FROM inventario_data WHERE fila_idx=%s AND tabla_nombre='Principal'", (fila_idx,)
    )
    return {"mensaje": f"Fila {fila_idx} eliminada"}
