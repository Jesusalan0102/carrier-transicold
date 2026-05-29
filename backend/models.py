from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date

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

class AsistenciaCreate(BaseModel):
    username: str
    fecha: date
    hora_checkin: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    distancia_metros: Optional[float] = None
    aprobado: bool = False
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class AsistenciaResponse(BaseModel):
    id: int
    username: str
    fecha: date
    hora_checkin: str
    latitud: Optional[float] = None
    longitud: Optional[float] = None
    distancia_metros: Optional[float] = None
    aprobado: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
