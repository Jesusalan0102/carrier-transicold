from fastapi import APIRouter, Depends, HTTPException
from db import execute_read, execute_write
import bcrypt
from pydantic import BaseModel
from auth import verify_token

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])

ROLES_PERMITIDOS = {"admin", "tecnico", "visor", "lider"}

class UserCreate(BaseModel):
    username: str
    password: str
    role: str
    nombre_completo: str = ""

class PasswordChange(BaseModel):
    new_password: str

class PerfilUpdate(BaseModel):
    foto_url: str = ""
    puesto: str = ""

class NombreUpdate(BaseModel):
    nombre_completo: str = ""

@router.get("/me")
def mi_perfil(current_user=Depends(verify_token)):
    """Devuelve foto_url, puesto y nombre_completo del usuario en sesion — accesible para cualquier rol."""
    rows = execute_read(
        "SELECT id, username, role, foto_url, puesto, nombre_completo FROM users WHERE username = %s",
        (current_user["username"],)
    )
    if not rows:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return rows[0]

@router.get("/")
def listar_usuarios(current_user=Depends(verify_token)):
    """Ver la lista es distinto a administrar usuarios: el líder la necesita
    para poder elegir a qué técnico asignarle una tarea, pero sigue sin
    poder crear/editar/eliminar usuarios (ver endpoints abajo, admin-only)."""
    if current_user["role"] not in ("admin", "visor", "lider"):
        raise HTTPException(status_code=403, detail="Acceso denegado")
    return execute_read(
        "SELECT id, username, role, foto_url, puesto, nombre_completo FROM users ORDER BY role, username"
    )

@router.put("/{user_id}/perfil")
def actualizar_perfil(user_id: int, data: PerfilUpdate, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    execute_write(
        "UPDATE users SET foto_url = %s, puesto = %s WHERE id = %s",
        (data.foto_url or None, data.puesto or None, user_id)
    )
    return {"mensaje": "Perfil actualizado correctamente"}

@router.put("/{user_id}/nombre")
def actualizar_nombre(user_id: int, data: NombreUpdate, current_user=Depends(verify_token)):
    """Permite al administrador definir el nombre real que se mostrará en gráficas y horarios."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    execute_write(
        "UPDATE users SET nombre_completo = %s WHERE id = %s",
        (data.nombre_completo.strip() or None, user_id)
    )
    return {"mensaje": "Nombre actualizado correctamente"}

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
    try:
        execute_write(
            "INSERT INTO users (username, password, role, nombre_completo) VALUES (%s,%s,%s,%s)",
            (user.username, hashed_password, user.role, user.nombre_completo.strip() or None)
        )
    except Exception as e:
        # Causa más probable: la columna `role` en MySQL es un ENUM fijo
        # (p.ej. ENUM('admin','tecnico','visor')) que no incluye este rol
        # todavía. Ver migración pendiente: ALTER TABLE users MODIFY COLUMN
        # role VARCHAR(20) ...
        raise HTTPException(
            status_code=500,
            detail=f"No se pudo crear el usuario. Es probable que la base de datos "
                   f"aún no acepte el rol '{user.role}' (columna role tipo ENUM sin "
                   f"actualizar). Detalle técnico: {e}"
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
