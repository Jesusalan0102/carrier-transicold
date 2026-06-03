from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
import bcrypt
from db import execute_read
from auth import create_access_token, verify_token

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

def check_password(plain: str, stored: str) -> bool:
    """
    Verifica la contraseña usando bcrypt directo (compatible con bcrypt 5.0.0).
    No usa passlib para evitar el error de incompatibilidad con bcrypt 5.0.0.
    Soporta hashes $2a$, $2b$, $2y$ generados por bcrypt o passlib.
    """
    try:
        stored_bytes = stored.encode("utf-8") if isinstance(stored, str) else stored
        plain_bytes = plain.encode("utf-8")
        # Normalizar prefijo $2y$ y $2a$ a $2b$ si es necesario
        if stored_bytes.startswith(b"$2y$") or stored_bytes.startswith(b"$2a$"):
            stored_bytes = b"$2b$" + stored_bytes[4:]
        return bcrypt.checkpw(plain_bytes, stored_bytes)
    except Exception as e:
        print(f"[auth] Error en check_password: {e}")
        return False

@router.post("/login")
async def login(credentials: LoginRequest):
    # 1. Buscar usuario en la BD
    rows = execute_read(
        "SELECT id, username, password, role FROM users WHERE username = %s LIMIT 1",
        (credentials.username,)
    )
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )

    user = rows[0]

    # 2. Verificar contraseña
    if not check_password(credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )

    # 3. Generar JWT con sub=username y role
    token = create_access_token(data={"sub": user["username"], "role": user["role"]})

    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user["username"],
        "role": user["role"]
    }

@router.get("/me")
async def read_users_me(current_user=Depends(verify_token)):
    return {"username": current_user["username"], "role": current_user["role"]}
