"""
models_asistencia.py
====================
FRAGMENTO para agregar a tu models.py existente.

Agrega estos modelos si aún no los tienes, o revisa que los campos
coincidan con los que ya tienes definidos.

CAMBIOS CLAVE vs. el modelo anterior:
  - AsistenciaRegistro ahora tiene el campo  `tipo`  ("entrada" | "salida")
  - AsistenciaRegistro ahora tiene el campo  `retardo_min`
  - AsistenciaConfig sin cambios

MIGRACIÓN (si usas Alembic):
    alembic revision --autogenerate -m "add_tipo_retardo_asistencia"
    alembic upgrade head

Si no usas Alembic, ejecuta directamente en tu BD:
    ALTER TABLE asistencia_registros ADD COLUMN tipo      VARCHAR DEFAULT 'entrada';
    ALTER TABLE asistencia_registros ADD COLUMN retardo_min INTEGER DEFAULT 0;
"""

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, Text
)
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()   # usa tu Base real — no declares una nueva


# ─────────────────────────────────────────────────────────────────────────────
# ASISTENCIA REGISTRO
# ─────────────────────────────────────────────────────────────────────────────
class AsistenciaRegistro(Base):
    """
    Cada fila = un check-in de ENTRADA o SALIDA.
    Un técnico puede tener exactamente 1 entrada y 1 salida por día.
    """
    __tablename__ = "asistencia_registros"

    id               = Column(Integer, primary_key=True, index=True)
    username         = Column(String, nullable=False, index=True)

    # ▶ NUEVO — "entrada" | "salida"
    tipo             = Column(String, nullable=False, default="entrada")

    fecha            = Column(String, nullable=False, index=True)  # "YYYY-MM-DD"
    hora_checkin     = Column(String, nullable=False)              # "HH:MM"

    lat              = Column(Float,   nullable=True)
    lon              = Column(Float,   nullable=True)
    precision_gps    = Column(Float,   nullable=True)
    distancia_metros = Column(Float,   nullable=True)

    aprobado         = Column(Boolean, default=True)

    # ▶ NUEVO — minutos de retardo sobre la hora de entrada programada
    retardo_min      = Column(Integer, default=0)

    created_at       = Column(DateTime, default=datetime.utcnow)


# ─────────────────────────────────────────────────────────────────────────────
# ASISTENCIA CONFIG (sin cambios)
# ─────────────────────────────────────────────────────────────────────────────
class AsistenciaConfig(Base):
    """Configuración global de geolocalización (1 sola fila)."""
    __tablename__ = "asistencia_config"

    id           = Column(Integer, primary_key=True)
    lat_fija     = Column(Float, default=32.5027)
    lon_fija     = Column(Float, default=-117.0037)
    radio_metros = Column(Integer, default=200)


# ─────────────────────────────────────────────────────────────────────────────
# HORARIO SEMANAL
# ─────────────────────────────────────────────────────────────────────────────
class Horario(Base):
    """
    Un registro = un técnico en un día específico.
    Almacena la hora de entrada y salida programada.
    Unicidad: (username, fecha).
    """
    __tablename__ = "horarios"

    id           = Column(Integer, primary_key=True, index=True)
    username     = Column(String, nullable=False, index=True)
    fecha        = Column(String, nullable=False, index=True)  # "YYYY-MM-DD"
    semana       = Column(String, nullable=False, index=True)  # "YYYY-MM-DD" lunes
    hora_entrada = Column(String, nullable=True)               # "HH:MM"
    hora_salida  = Column(String, nullable=True)               # "HH:MM"


# ─────────────────────────────────────────────────────────────────────────────
# MIGRACIÓN MANUAL (sin Alembic)
# Pega esto en un script Python y ejecútalo UNA VEZ:
# ─────────────────────────────────────────────────────────────────────────────
MIGRACION_SQL = """
-- 1. Agregar columna 'tipo' si no existe (SQLite)
ALTER TABLE asistencia_registros ADD COLUMN tipo VARCHAR DEFAULT 'entrada';

-- 2. Agregar columna 'retardo_min' si no existe
ALTER TABLE asistencia_registros ADD COLUMN retardo_min INTEGER DEFAULT 0;

-- 3. Marcar registros existentes como 'entrada' (retrocompatibilidad)
UPDATE asistencia_registros SET tipo = 'entrada' WHERE tipo IS NULL OR tipo = '';

-- 4. Crear tabla horarios si no existe
CREATE TABLE IF NOT EXISTS horarios (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    username     TEXT NOT NULL,
    fecha        TEXT NOT NULL,
    semana       TEXT NOT NULL,
    hora_entrada TEXT,
    hora_salida  TEXT,
    UNIQUE(username, fecha)
);

-- 5. Crear tabla asistencia_config si no existe
CREATE TABLE IF NOT EXISTS asistencia_config (
    id           INTEGER PRIMARY KEY,
    lat_fija     REAL DEFAULT 32.5027,
    lon_fija     REAL DEFAULT -117.0037,
    radio_metros INTEGER DEFAULT 200
);
"""

# Para ejecutarlo:
# from database import engine
# with engine.connect() as conn:
#     for stmt in MIGRACION_SQL.strip().split(';'):
#         stmt = stmt.strip()
#         if stmt:
#             conn.execute(stmt)
#     conn.commit()
