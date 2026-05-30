from fastapi import APIRouter, Depends, HTTPException
from db import execute_read, execute_write, execute_write_with_id
from auth import verify_token
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/asignaciones", tags=["asignaciones"])

class AsignacionUpdate(BaseModel):
    estado: Optional[str] = None

@router.get("/")
def get_asignaciones(current_user=Depends(verify_token)):
    try:
        if current_user["role"] == "admin":
            return execute_read("SELECT * FROM asignaciones ORDER BY id DESC")
        return execute_read(
            "SELECT * FROM asignaciones WHERE tecnico=%s ORDER BY id DESC",
            (current_user["username"],)
        )
    except Exception as e:
        print(f"Error en get_asignaciones: {e}")
        return []

@router.put("/{asignacion_id}")
def update_asignacion(asignacion_id: int, data: AsignacionUpdate, current_user=Depends(verify_token)):
    existing = execute_read("SELECT * FROM asignaciones WHERE id=%s", (asignacion_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    ex = existing[0]
    if current_user["role"] not in ["admin", "supervisor"] and ex.get("tecnico") != current_user["username"]:
        raise HTTPException(status_code=403, detail="No autorizado")
    if data.estado:
        execute_write("UPDATE asignaciones SET estado=%s WHERE id=%s", (data.estado, asignacion_id))
    rows = execute_read("SELECT * FROM asignaciones WHERE id=%s", (asignacion_id,))
    return rows[0] if rows else {}
