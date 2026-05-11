from fastapi import APIRouter, Depends, HTTPException
from db import execute_read, execute_write
from auth import verify_token
from pydantic import BaseModel

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])

class UserCreate(BaseModel):
    username: str
    password: str
    role: str

@router.get("/")
def listar_usuarios(current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    return execute_read("SELECT id, username, role FROM users ORDER BY role, username")

@router.post("/")
def crear_usuario(user: UserCreate, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    execute_write(
        "INSERT INTO users (username, password, role) VALUES (%s,%s,%s)",
        (user.username, user.password, user.role)
    )
    return {"mensaje": "Usuario creado"}

@router.put("/{user_id}")
def actualizar_usuario(user_id: int, user: UserCreate, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    execute_write(
        "UPDATE users SET username=%s, password=%s, role=%s WHERE id=%s",
        (user.username, user.password, user.role, user_id)
    )
    return {"mensaje": "Usuario actualizado"}

@router.delete("/{user_id}")
def eliminar_usuario(user_id: int, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    execute_write("DELETE FROM users WHERE id=%s", (user_id,))
    return {"mensaje": "Usuario eliminado"}