from fastapi import APIRouter, HTTPException
from db import execute_read
from models import LoginRequest, TokenResponse
from auth import create_access_token

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest):
    users = execute_read(
        "SELECT username, role FROM users WHERE username=%s AND password=%s",
        (login_data.username, login_data.password)
    )
    if not users:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    user = users[0]
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return {
        "access_token": token,
        "role": user["role"],
        "username": user["username"]
    }
