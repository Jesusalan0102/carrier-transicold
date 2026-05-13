from fastapi import APIRouter, Depends, HTTPException
from db import execute_read, execute_write
from auth import verify_token, pwd_context
from pydantic import BaseModel

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])

ROLES_PERMITIDOS = {"admin", "tecnico", "visor"}

class UserCreate(BaseModel):
    username: str
    password: str
    role: str

class UserUpdate(BaseModel):
    username: str
    password: str
    role: str

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
    
    # Verificar si el usuario ya existe
    existing = execute_read("SELECT id FROM users WHERE username = %s", (user.username,))
    if existing:
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")
    
    # Hashear la contraseña
    hashed_password = pwd_context.hash(user.password)
    
    execute_write(
        "INSERT INTO users (username, password, role) VALUES (%s,%s,%s)",
        (user.username, hashed_password, user.role)
    )
    return {"mensaje": "Usuario creado"}

@router.put("/{user_id}")
def actualizar_usuario(user_id: int, user: UserUpdate, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    if user.role not in ROLES_PERMITIDOS:
        raise HTTPException(status_code=400, detail=f"Rol inválido. Usa: {ROLES_PERMITIDOS}")
    
    hashed_password = pwd_context.hash(user.password)
    execute_write(
        "UPDATE users SET username=%s, password=%s, role=%s WHERE id=%s",
        (user.username, hashed_password, user.role, user_id)
    )
    return {"mensaje": "Usuario actualizado"}

@router.delete("/{user_id}")
def eliminar_usuario(user_id: int, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    execute_write("DELETE FROM users WHERE id=%s", (user_id,))
    return {"mensaje": "Usuario eliminado"}