from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import Asignacion, AsignacionCreate, AsignacionUpdate, User
from auth import get_current_user

router = APIRouter(prefix="/api/asignaciones", tags=["asignaciones"])

@router.get("/")
def get_asignaciones(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.rol == "admin":
        asignaciones = db.query(Asignacion).all()
    else:
        asignaciones = db.query(Asignacion).filter(Asignacion.usuario_id == current_user.id).all()
    return asignaciones if asignaciones else []

@router.post("/")
def create_asignacion(
    asignacion: AsignacionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.rol not in ["admin", "supervisor"]:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    nueva = Asignacion(**asignacion.model_dump())
    db.add(nueva)
    db.commit()
    db.refresh(nueva)
    return nueva

@router.put("/{asignacion_id}")
def update_asignacion(
    asignacion_id: int,
    asignacion: AsignacionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    existing = db.query(Asignacion).filter(Asignacion.id == asignacion_id).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    
    if current_user.rol not in ["admin", "supervisor"] and existing.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado")
    
    for key, value in asignacion.model_dump(exclude_unset=True).items():
        setattr(existing, key, value)
    
    db.commit()
    db.refresh(existing)
    return existing
