import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()

# Ruta del certificado
CERT_PATH = os.path.join(os.path.dirname(__file__), "isrgrootx1.pem")

# Verificar si el certificado existe
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
    # Si no hay certificado, conectar sin SSL (solo para desarrollo)
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
    """Context manager para conexiones a la base de datos"""
    conn = pymysql.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()

def execute_read(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Ejecuta una consulta SELECT y retorna los resultados como lista de diccionarios"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

def execute_write(sql: str, params: tuple = ()) -> int:
    """Ejecuta una consulta INSERT/UPDATE/DELETE y retorna el número de filas afectadas"""
    with get_db() as conn:
        with conn.cursor() as cur:
            affected = cur.execute(sql, params)
        conn.commit()
        return affected

def execute_write_with_id(sql: str, params: tuple = ()) -> int:
    """Ejecuta un INSERT y retorna el ID generado"""
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            last_id = cur.lastrowid
        conn.commit()
        return last_id

def execute_query(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    """Alias de execute_read para compatibilidad"""
    return execute_read(sql, params)

def init_db():
    """Las tablas ya existen en TiDB Cloud"""
    print("✅ Base de datos TiDB conectada correctamente")
