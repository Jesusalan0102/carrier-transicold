import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

# Ruta del certificado
CERT_PATH = os.path.join(os.path.dirname(__file__), "isrgrootx1.pem")

# Verificar si el certificado existe, si no, deshabilitar SSL temporalmente
if os.path.exists(CERT_PATH):
    DB_CONFIG = {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", 4000)),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
        "autocommit": True,
        "cursorclass": DictCursor,
        "ssl": {"ca": CERT_PATH}
    }
else:
    # Si no hay certificado, conectar sin SSL
    DB_CONFIG = {
        "host": os.getenv("DB_HOST"),
        "port": int(os.getenv("DB_PORT", 4000)),
        "user": os.getenv("DB_USER"),
        "password": os.getenv("DB_PASSWORD"),
        "database": os.getenv("DB_NAME"),
        "autocommit": True,
        "cursorclass": DictCursor,
    }

@contextmanager
def get_db():
    conn = pymysql.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()

def execute_read(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Ejecuta una consulta SELECT y retorna los resultados"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

def execute_write(sql: str, params: tuple = ()):
    """Ejecuta una consulta INSERT/UPDATE/DELETE"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()

def execute_query(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Alias de execute_read para compatibilidad"""
    return execute_read(sql, params)

def init_db():
    """Las tablas ya existen en TiDB Cloud"""
    pass
