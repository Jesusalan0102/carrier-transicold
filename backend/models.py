from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Time, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base
from pydantic import BaseModel
from typing import Optional

# ====================
# MODELOS SQLALCHEMY (Base de Datos)
# ====================

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    is_active = Column(Boolean, default=True)
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
    dia_semana = Column(Integer, nullable=False)  # 0=Lunes, 1=Martes, ..., 6=Domingo
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
    tipo = Column(String(20), nullable=False)  # 'entrada' o 'salida'
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
    estado = Column(String(50), default="pendiente")  # pendiente, en_progreso, completada, atrasada
    usuario_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relación con usuario
    usuario = relationship("User", back_populates="asignaciones")


# ====================
# MODELOS PYDANTIC (Validación de API)
# ====================

# Modelos para Asistencia
class AsistenciaResponse(BaseModel):
    id: int
    user_id: int
    fecha: datetime
    tipo: str
    latitud: Optional[str] = None
    longitud: Optional[str] = None
    observacion: Optional[str] = None
    
    class Config:
        from_attributes = True


class AsistenciaConfigResponse(BaseModel):
    id: int
    user_id: int
    tolerancia_minutos: int
    requiere_justificacion: bool
    
    class Config:
        from_attributes = True


class HorarioResponse(BaseModel):
    id: int
    user_id: int
    dia_semana: int
    hora_entrada: str
    hora_salida: str
    
    class Config:
        from_attributes = True


# Modelos para Asignaciones
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


class AsignacionResponse(BaseModel):
    id: int
    titulo: str
    descripcion: Optional[str] = None
    fecha_creacion: datetime
    fecha_entrega: Optional[datetime] = None
    estado: str
    usuario_id: int
    
    class Config:
        from_attributes = True


# Modelos para Usuario
class UserCreate(BaseModel):
    username: str
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
