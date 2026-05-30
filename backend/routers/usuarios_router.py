from fastapi import APIRouter, Depends, HTTPException
from db import execute_read, execute_write, execute_write_with_id
from auth import verify_token, get_password_hash
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])

class UserResponse(BaseModel):
    id: int
    username: str
    is_active: bool
    rol: str

@router.get("/")
def get_usuarios(current_user=Depends(verify_token)):
    try:
        rows = execute_read("SELECT id, username, is_active, role as rol FROM users")
        return rows if rows else []
    except Exception as e:
        print(f"Error en get_usuarios: {e}")
        return []

@router.get("/activos")
def get_usuarios_activos(current_user=Depends(verify_token)):
    try:
        rows = execute_read("SELECT id, username, is_active, role as rol FROM users WHERE is_active=1")
        return rows if rows else []
    except Exception as e:
        return []

@router.post("/")
def create_usuario(
    username: str,
    password: str,
    rol: str = "tecnico",
    current_user=Depends(verify_token)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")
    existing = execute_read("SELECT id FROM users WHERE username=%s", (username,))
    if existing:
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    hashed = get_password_hash(password)
    new_id = execute_write_with_id(
        "INSERT INTO users (username, password, role, is_active) VALUES (%s,%s,%s,1)",
        (username, hashed, rol)
    )
    return {"id": new_id, "username": username, "rol": rol, "is_active": True}
