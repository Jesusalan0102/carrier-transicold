from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Time
from sqlalchemy.orm import relationship
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Horario(Base):
    __tablename__ = "horarios"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    dia_semana = Column(Integer)  # 0=Lunes, 1=Martes, etc.
    hora_entrada = Column(Time)
    hora_salida = Column(Time)
    
    user = relationship("User", back_populates="horarios")

class AsistenciaConfig(Base):
    __tablename__ = "asistencia_config"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    tolerancia_minutos = Column(Integer, default=15)
    requiere_justificacion = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="config")

class AsistenciaRegistro(Base):
    __tablename__ = "asistencia_registros"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    fecha = Column(DateTime, default=datetime.utcnow)
    tipo = Column(String(20))  # 'entrada' o 'salida'
    latitud = Column(String(20), nullable=True)
    longitud = Column(String(20), nullable=True)
    observacion = Column(String(500), nullable=True)
    
    user = relationship("User", back_populates="registros")

# Agregar relaciones a User
User.horarios = relationship("Horario", back_populates="user")
User.config = relationship("AsistenciaConfig", back_populates="user", uselist=False)
User.registros = relationship("AsistenciaRegistro", back_populates="user")
