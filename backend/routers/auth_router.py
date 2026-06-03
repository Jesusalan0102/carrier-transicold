from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from db import execute_read
from auth import create_access_token, verify_token, verify_password

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

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

    # 2. Verificar contraseña — compatible con passlib y bcrypt directo
    try:
        password_ok = verify_password(credentials.password, user["password"])
    except Exception:
        password_ok = False

    if not password_ok:
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
