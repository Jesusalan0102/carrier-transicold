from fastapi import APIRouter, Depends, HTTPException
from db import execute_read, execute_write
import bcrypt
from pydantic import BaseModel
from auth import verify_token

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])

ROLES_PERMITIDOS = {"admin", "tecnico", "visor"}

class UserCreate(BaseModel):
    username: str
    password: str
    role: str

class PasswordChange(BaseModel):
    new_password: str

@router.get("/")
def listar_usuarios(current_user=Depends(verify_token)):
    if current_user["role"] not in ("admin", "visor"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return execute_read("SELECT id, username, role FROM users ORDER BY role, username")

@router.post("/")
def crear_usuario(user: UserCreate, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    if user.role not in ROLES_PERMITIDOS:
        raise HTTPException(status_code=400, detail=f"Rol inválido. Usa: {ROLES_PERMITIDOS}")
    existing = execute_read("SELECT id FROM users WHERE username = %s", (user.username,))
    if existing:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    hashed_password = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    execute_write(
        "INSERT INTO users (username, password, role) VALUES (%s,%s,%s)",
        (user.username, hashed_password, user.role)
    )
    return {"mensaje": "Usuario creado", "username": user.username, "role": user.role}

@router.put("/{user_id}/password")
def cambiar_password(user_id: int, data: PasswordChange, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    if not data.new_password or len(data.new_password) < 4:
        raise HTTPException(status_code=400, detail="La contraseña debe tener al menos 4 caracteres")
    hashed = bcrypt.hashpw(data.new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    execute_write("UPDATE users SET password = %s WHERE id = %s", (hashed, user_id))
    return {"mensaje": "Contraseña actualizada correctamente"}

@router.delete("/{user_id}")
def eliminar_usuario(user_id: int, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    execute_write("DELETE FROM users WHERE id=%s", (user_id,))
    return {"mensaje": "Usuario eliminado"}
