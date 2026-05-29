from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Time, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from pydantic import BaseModel
from typing import Optional

# ====================
# MODELOS SQLALCHEMY
# ====================

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    rol = Column(String(50), default="tecnico")  # admin, tecnico, supervisor
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    horarios = relationship("Horario", back_populates="user", cascade="all, delete-orphan")
    config = relationship("AsistenciaConfig", back_populates="user", uselist=False, cascade="all, delete-orphan")
    registros = relationship("AsistenciaRegistro", back_populates="user", cascade="all, delete-orphan")
    asignaciones = relationship("Asignacion", back_populates="usuario", cascade="all, delete-orphan")

class Horario(Base):
    __tablename__ = "horarios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dia_semana = Column(Integer, nullable=False)
    hora_entrada = Column(Time, nullable=False)
    hora_salida = Column(Time, nullable=False)
    
    user = relationship("User", back_populates="horarios")

class AsistenciaConfig(Base):
    __tablename__ = "asistencia_config"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    tolerancia_minutos = Column(Integer, default=15)
    requiere_justificacion = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="config")

class AsistenciaRegistro(Base):
    __tablename__ = "asistencia_registros"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    fecha = Column(DateTime, default=datetime.utcnow)
    tipo = Column(String(20), nullable=False)
    latitud = Column(String(20), nullable=True)
    longitud = Column(String(20), nullable=True)
    observacion = Column(Text, nullable=True)
    
    user = relationship("User", back_populates="registros")

class Asignacion(Base):
    __tablename__ = "asignaciones"
    
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(200), nullable=False)
    descripcion = Column(Text, nullable=True)
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_entrega = Column(DateTime, nullable=True)
    estado = Column(String(50), default="pendiente")
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    usuario = relationship("User", back_populates="asignaciones")

# ====================
# MODELOS PYDANTIC
# ====================

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    rol: str
    
    class Config:
        from_attributes = True

class AsignacionCreate(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    fecha_entrega: Optional[datetime] = None
    usuario_id: int
    estado: Optional[str] = "pendiente"

class AsignacionUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    fecha_entrega: Optional[datetime] = None
    estado: Optional[str] = None
