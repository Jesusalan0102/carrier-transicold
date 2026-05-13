from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from db import execute_read
from pydantic import BaseModel
import bcrypt
from jose import jwt
from datetime import datetime, timedelta
import os

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()

# Configuración
# bcrypt directo (compatible con Python 3.14)
SECRET_KEY = os.getenv("SECRET_KEY", "carrier_secret_key_2024_change_in_production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    role: str
    username: str

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest):
    # Buscar usuario
    users = execute_read(
        "SELECT username, password, role FROM users WHERE username = %s",
        (login_data.username,)
    )
    
    if not users:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    user = users[0]
    
    # Verificar contraseña usando bcrypt
    if not bcrypt.checkpw(login_data.password.encode("utf-8"), user["password"].encode("utf-8")):
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    # Crear token
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    
    return {
        "access_token": token,
        "role": user["role"],
        "username": user["username"]
    }