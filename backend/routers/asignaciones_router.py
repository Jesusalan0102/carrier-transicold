from fastapi import APIRouter, Depends, HTTPException
from db import execute_read, execute_write, execute_write_with_id
from auth import verify_token
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

router = APIRouter(prefix="/api/asignaciones", tags=["asignaciones"])

class AsignacionCreate(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    fecha_entrega: Optional[datetime] = None
    usuario_id: int
    estado: Optional[str] = "pendiente"

class AsignacionUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_entrega: Optional[datetime] = None
    estado: Optional[str] = None

@router.get("/")
def get_asignaciones(current_user=Depends(verify_token)):
    if current_user["role"] == "admin":
        return execute_read("SELECT * FROM asignaciones ORDER BY fecha_creacion DESC")
    return execute_read(
        "SELECT a.* FROM asignaciones a JOIN users u ON a.usuario_id=u.id WHERE u.username=%s ORDER BY a.fecha_creacion DESC",
        (current_user["username"],)
    )

@router.post("/")
def create_asignacion(data: AsignacionCreate, current_user=Depends(verify_token)):
    if current_user["role"] not in ["admin", "supervisor"]:
        raise HTTPException(status_code=403, detail="No autorizado")
    new_id = execute_write_with_id(
        "INSERT INTO asignaciones (titulo, descripcion, fecha_entrega, usuario_id, estado, fecha_creacion) VALUES (%s,%s,%s,%s,%s,%s)",
        (data.titulo, data.descripcion, data.fecha_entrega, data.usuario_id, data.estado, datetime.now())
    )
    rows = execute_read("SELECT * FROM asignaciones WHERE id=%s", (new_id,))
    return rows[0] if rows else {"id": new_id}

@router.put("/{asignacion_id}")
def update_asignacion(asignacion_id: int, data: AsignacionUpdate, current_user=Depends(verify_token)):
    existing = execute_read("SELECT * FROM asignaciones WHERE id=%s", (asignacion_id,))
    if not existing:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    ex = existing[0]
    if current_user["role"] not in ["admin", "supervisor"]:
        user = execute_read("SELECT id FROM users WHERE username=%s", (current_user["username"],))
        if not user or ex.get("usuario_id") != user[0]["id"]:
            raise HTTPException(status_code=403, detail="No autorizado")
    fields = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    if fields:
        sets = ", ".join(f"{k}=%s" for k in fields)
        execute_write(f"UPDATE asignaciones SET {sets} WHERE id=%s", (*fields.values(), asignacion_id))
    rows = execute_read("SELECT * FROM asignaciones WHERE id=%s", (asignacion_id,))
    return rows[0] if rows else {}
