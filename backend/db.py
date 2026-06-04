# backend/db.py
import os
import pymysql
from dbutils.pooled_db import PooledDB  # ← Importante: dbutils en minúsculas

pool = None

def _run_migrations():
    """Aplica migraciones de columnas nuevas sin romper si ya existen."""
    conn = pool.connection()
    try:
        with conn.cursor() as cur:
            # Agrega retardo_min a registros_asistencia si no existe
            cur.execute("""
                SELECT COUNT(*) FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                  AND TABLE_NAME   = 'registros_asistencia'
                  AND COLUMN_NAME  = 'retardo_min'
            """)
            row = cur.fetchone()
            count = row[0] if isinstance(row, tuple) else list(row.values())[0]
            if count == 0:
                cur.execute(
                    "ALTER TABLE registros_asistencia ADD COLUMN retardo_min INT NOT NULL DEFAULT 0"
                )
                conn.commit()
                print("✅ Migración: columna retardo_min añadida a registros_asistencia")
    except Exception as e:
        print(f"⚠️  Migración omitida: {e}")
    finally:
        conn.close()


def init_db():
    global pool
    if pool is not None:
        return
    
    pool = PooledDB(
        creator=pymysql,
        maxconnections=15,
        mincached=2,
        maxcached=5,
        blocking=True,
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        charset='utf8mb4',
        # ssl={"ca": "/etc/ssl/certs/ca-certificates.crt"}  # Descomenta si CleverCloud requiere SSL
    )
    print("✅ Pool de conexiones DB inicializado correctamente")

    # ── Migraciones automáticas (idempotentes) ────────────────────────────────
    _run_migrations()


def execute_read(sql: str, params=None):
    """Ejecuta consultas SELECT"""
    conn = pool.connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()
    finally:
        conn.close()


def execute_write(sql: str, params=None):
    """Ejecuta INSERT, UPDATE, DELETE"""
    conn = pool.connection()
    try:
        with conn.cursor() as cursor:
            affected = cursor.execute(sql, params or ())
            conn.commit()
            return affected
    finally:
        conn.close()


def execute_write_with_id(sql: str, params=None):
    """Ejecuta INSERT y devuelve el lastrowid del registro creado."""
    conn = pool.connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()


def get_db_connection():
    """
    Devuelve una conexión directa del pool.
    El llamador es responsable de llamar connection.close() en un bloque finally.
    Usado por asistencia/routes.py y reporte_router.py que manejan
    el cursor y commit manualmente.
    """
    if pool is None:
        print("❌ get_db_connection: el pool no está inicializado")
        return None
    try:
        return pool.connection()
    except Exception as e:
        print(f"❌ Error obteniendo conexión del pool: {e}")
        return None
