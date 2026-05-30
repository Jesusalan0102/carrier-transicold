from fastapi import APIRouter, Depends, HTTPException
from db import execute_read, execute_write, execute_write_with_id
from auth import verify_token, get_password_hash

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])

@router.get("/")
def get_usuarios(current_user=Depends(verify_token)):
    try:
        return execute_read("SELECT id, username, role FROM users") or []
    except Exception as e:
        print(f"Error en get_usuarios: {e}")
        return []

@router.get("/activos")
def get_usuarios_activos(current_user=Depends(verify_token)):
    try:
        return execute_read("SELECT id, username, role FROM users WHERE role != 'inactivo'") or []
    except Exception as e:
        return []

@router.post("/")
def create_usuario(username: str, password: str, rol: str = "tecnico", current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")
    if execute_read("SELECT id FROM users WHERE username=%s", (username,)):
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    import bcrypt
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    new_id = execute_write_with_id(
        "INSERT INTO users (username, password, role) VALUES (%s,%s,%s)",
        (username, hashed, rol)
    )
    return {"id": new_id, "username": username, "role": rol}
