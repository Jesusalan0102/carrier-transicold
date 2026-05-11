from fastapi import APIRouter, Depends, HTTPException
from db import execute_read, execute_write
from auth import verify_token
from pydantic import BaseModel

router = APIRouter(prefix="/api/comentarios", tags=["comentarios"])

class ComentarioCreate(BaseModel):
    asignacion_id: int
    comentario: str

# ── LISTAR TODOS (admin) ───────────────────────────────────────────────────
@router.get("/")
def listar_comentarios(current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    return execute_read(
        """SELECT ca.*, a.unidad, a.actividad_id
           FROM comentarios_actividades ca
           LEFT JOIN asignaciones a ON ca.asignacion_id = a.id
           ORDER BY ca.fecha DESC LIMIT 100"""
    )

# ── POR ASIGNACIÓN ─────────────────────────────────────────────────────────
@router.get("/{asignacion_id}")
def comentarios_asignacion(asignacion_id: int, current_user=Depends(verify_token)):
    return execute_read(
        "SELECT * FROM comentarios_actividades WHERE asignacion_id=%s ORDER BY fecha DESC",
        (asignacion_id,)
    )

# ── CREAR ──────────────────────────────────────────────────────────────────
@router.post("/")
def crear_comentario(data: ComentarioCreate, current_user=Depends(verify_token)):
    if not data.comentario.strip():
        raise HTTPException(status_code=400, detail="El comentario no puede estar vacío")
    execute_write(
        "INSERT INTO comentarios_actividades (asignacion_id, tecnico, comentario) VALUES (%s,%s,%s)",
        (data.asignacion_id, current_user["username"], data.comentario.strip())
    )
    return {"mensaje": "Comentario guardado"}
