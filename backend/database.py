from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
import os

# Obtener variables de entorno (con tus credenciales actuales como fallback)
DB_HOST = os.getenv("DB_HOST", "gateway01.us-east-1.prod.aws.tidbcloud.com")
DB_PORT = os.getenv("DB_PORT", "4000")
DB_USER = os.getenv("DB_USER", "4BgYs96t9XXhCMS.root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "YZcSUhQ5H7Gx9vLk")
DB_NAME = os.getenv("DB_NAME", "carrier_db")

# TiDB Cloud requiere SSL/TLS
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?ssl_ca=/etc/ssl/certs/ca-certificates.crt"

# Configuración SSL para TiDB Cloud
ssl_args = {
    "ssl": {
        "ca": "/etc/ssl/certs/ca-certificates.crt"
    }
}

# Crear engine con SSL y configuraciones para la nube
engine = create_engine(
    DATABASE_URL,
    connect_args=ssl_args,
    pool_pre_ping=True,      # Verifica conexiones antes de usarlas
    pool_recycle=3600,       # Recicla conexiones cada hora
    pool_size=10,            # Tamaño del pool de conexiones
    max_overflow=20          # Conexiones extra permitidas
)

# Crear sesión local
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()

# Dependencia para obtener la sesión de BD
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
