import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from typing import List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

# Ruta del certificado (debe estar en backend/isrgrootx1.pem)
CERT_PATH = os.path.join(os.path.dirname(__file__), "isrgrootx1.pem")

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 4000)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "autocommit": True,
    "cursorclass": DictCursor,
    "ssl": {
        "ca": CERT_PATH,
        "check_hostname": True
    }
}

@contextmanager
def get_db():
    conn = pymysql.connect(**DB_CONFIG)
    try:
        yield conn
    finally:
        conn.close()

def execute_query(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

def execute_write(sql: str, params: tuple = ()):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()

def execute_read(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    return execute_query(sql, params)

def init_db():
    # Las tablas ya existen en TiDB Cloud
    pass
