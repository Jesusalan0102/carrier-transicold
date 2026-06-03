from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, APIRouter
from fastapi.security import OAuth2PasswordBearer
import os

SECRET_KEY = os.getenv("SECRET_KEY", "carrier_secret_key_2024_change_in_production")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")

# FIX Bug 5: se amplió el tiempo de expiración de 30 min a 8 horas para evitar
# que el usuario reciba un 401 a mitad de una jornada de trabajo.
# Si tu política de seguridad requiere sesiones más cortas, ajusta este valor.
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 480))  # 8 horas

pwd_context   = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


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


# ── FIX Bug 5: endpoint /api/auth/refresh ────────────────────────────────────
# Permite al frontend renovar el token sin forzar un re-login completo.
# El frontend debe llamar este endpoint antes de que expire el token actual,
# o detectar el 401 y hacer el refresh automáticamente.
#
# Uso desde el frontend:
#   const res = await fetch('/api/auth/refresh', {
#       method: 'POST',
#       headers: { 'Authorization': 'Bearer ' + window.token }
#   });
#   if (res.ok) {
#       const data = await res.json();
#       localStorage.setItem('access_token', data.access_token);
#       window.token = data.access_token;
#   }
#
# Este router se debe incluir en main.py con:
#   app.include_router(refresh_router, prefix="/api/auth", tags=["auth"])
# Ya está incluido en el main.py parcheado.

refresh_router = APIRouter()

@refresh_router.post("/refresh")
def refresh_token(current_user: dict = Depends(verify_token)):
    """
    Recibe un JWT válido (aún no expirado) y devuelve uno nuevo con
    el tiempo de expiración reiniciado. No requiere contraseña.
    """
    new_token = create_access_token(
        data={"sub": current_user["username"], "role": current_user["role"]}
    )
    return {
        "access_token": new_token,
        "token_type": "bearer",
        "username": current_user["username"],
        "role": current_user["role"],
    }
