from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str

class UserCreate(BaseModel):
    username: str
    password: str
    role: str

class UnidadCreate(BaseModel):
    unit_number: str
    id_lote: str
    vin_number: Optional[str] = ""
    reefer_serial: Optional[str] = ""
    reefer_model: Optional[str] = ""
    evaporator_serial_mjs11: Optional[str] = ""
    evaporator_serial_mjd22: Optional[str] = ""
    engine_serial: Optional[str] = ""
    compressor_serial: Optional[str] = ""
    generator_serial: Optional[str] = ""
    battery_charger_serial: Optional[str] = ""

class AsignacionCreate(BaseModel):
    unidad: str
    actividad_id: str
    tecnico: str
    estado: str = "pendiente"

class AsignacionUpdate(BaseModel):
    estado: Optional[str] = None
    tecnico: Optional[str] = None
    actividad_id: Optional[str] = None
    comentario: Optional[str] = None

class TicketCreate(BaseModel):
    unit_number: str
    vin_number: Optional[str] = ""
    descripcion: str
    tecnico: str

class TicketReport(BaseModel):
    reporte: str

class InventarioSave(BaseModel):
    filas: List[dict]
    columnas: List[str]

class CampoTVCreate(BaseModel):
    campo_nombre: str

class Asistencia(Base):
    __tablename__ = "asistencia"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, index=True)
    fecha = Column(Date, index=True)
    hora_checkin = Column(String)
    latitud = Column(Float, nullable=True)
    longitud = Column(Float, nullable=True)
    distancia_metros = Column(Float, nullable=True)
    aprobado = Column(Boolean, default=False)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
