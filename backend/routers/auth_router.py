import os
from fastapi import APIRouter, HTTPException, Depends
from db import execute_read
from pydantic import BaseModel
from auth import create_access_token, authenticate_user

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    role: str
    username: str

@router.post("/login", response_model=TokenResponse)
def login(login_data: LoginRequest):
    user = authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return {
        "access_token": token,
        "role": user["role"],
        "username": user["username"]
    }