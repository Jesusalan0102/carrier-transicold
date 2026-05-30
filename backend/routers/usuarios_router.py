from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import User, UserResponse
from auth import get_current_user, get_password_hash

router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])

@router.get("/")
def get_usuarios(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retorna lista de usuarios (SIEMPRE retorna un array)"""
    try:
        usuarios = db.query(User).all()
        # ✅ Aseguramos que siempre retornamos una lista
        return [UserResponse.model_validate(u) for u in usuarios] if usuarios else []
    except Exception as e:
        print(f"Error en get_usuarios: {e}")
        return []  # Siempre retornar array aunque haya error

@router.get("/activos")
def get_usuarios_activos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    usuarios = db.query(User).filter(User.is_active == True).all()
    return [UserResponse.model_validate(u) for u in usuarios] if usuarios else []

@router.post("/")
def create_usuario(
    username: str,
    password: str,
    rol: str = "tecnico",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.rol != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")
    
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Usuario ya existe")
    
    new_user = User(
        username=username,
        hashed_password=get_password_hash(password),
        rol=rol
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return UserResponse.model_validate(new_user)
