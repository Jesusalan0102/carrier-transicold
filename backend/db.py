import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
from dbutils.pooled_db import PooledDB

load_dotenv()

# Ruta del certificado
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
        "check_hostname": True,
    },
}

# Pool global — el SSL handshake se paga UNA sola vez por conexión,
# y las conexiones se reutilizan entre requests.
#
# Parámetros clave:
#   mincached  – conexiones precalentadas al arrancar
#   maxcached  – máximo de conexiones ociosas en el pool
#   maxconnections – límite absoluto (0 = sin límite)
#   blocking   – espera si el pool está lleno (True) en vez de lanzar error
def _create_pool() -> PooledDB:
    missing = [k for k in ("DB_HOST", "DB_USER", "DB_PASSWORD", "DB_NAME") if not os.getenv(k)]
    if missing:
        raise EnvironmentError(f"Faltan variables de entorno: {', '.join(missing)}")
    return PooledDB(
        creator=pymysql,
        mincached=2,
        maxcached=5,
        maxconnections=10,
        blocking=True,
        ping=1,           # verifica la conexión antes de entregarla
        **DB_CONFIG,
    )

_pool = _create_pool()


@contextmanager
def get_db():
    """Obtiene una conexión del pool y la devuelve al terminar."""
    conn = _pool.connection()
    try:
        yield conn
    finally:
        conn.close()  # devuelve al pool, NO cierra el socket real


def execute_read(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def execute_write(sql: str, params: tuple = ()):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()


def init_db():
    # Las tablas ya existen en TiDB Cloud
    pass
