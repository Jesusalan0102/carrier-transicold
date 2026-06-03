from datetime import datetime, timedelta
from typing import Optional
import bcrypt as _bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import os

SECRET_KEY = os.getenv("SECRET_KEY", "carrier_secret_key_2024_change_in_production")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 480))  # 8 horas

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_password_hash(password: str) -> str:
    """Genera un hash bcrypt de la contraseña."""
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica contraseña contra hash bcrypt (compatible con hashes generados por passlib)."""
    try:
        return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta if expires_delta else timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(credentials: str = Depends(oauth2_scheme)) -> dict:
    """Dependencia ligera — solo decodifica el JWT, sin tocar la BD."""
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str     = payload.get("role", "tecnico")
        if username is None:
            raise exc
        return {"username": username, "role": role}
    except JWTError:
        raise exc


async def get_current_user(credentials: str = Depends(oauth2_scheme)) -> dict:
    """Alias de verify_token — usado por módulos de asistencia."""
    return verify_token(credentials)


# ── Router principal de autenticación ────────────────────────────────────────
router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(data: LoginRequest):
    """
    Autentica con username + password y devuelve un JWT.
    Compatible con hashes generados por passlib[bcrypt] ya existentes en la BD.
    """
    from db import execute_read
    rows = execute_read(
        "SELECT id, username, password, role FROM users WHERE username = %s",
        (data.username,)
    )
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )
    user = rows[0]
    if not verify_password(data.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
        )
    token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "username": user["username"],
        "role": user["role"],
    }


# ── Refresh router ────────────────────────────────────────────────────────────
refresh_router = APIRouter()

@refresh_router.post("/refresh")
def refresh_token(current_user: dict = Depends(verify_token)):
    """Renueva el JWT sin requerir contraseña."""
    new_token = create_access_token(
        data={"sub": current_user["username"], "role": current_user["role"]}
    )
    return {
        "access_token": new_token,
        "token_type": "bearer",
        "username": current_user["username"],
        "role": current_user["role"],
    }
