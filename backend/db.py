# backend/db.py
import os
import pymysql
from dbutils.pooled_db import PooledDB   # ← Cambiado aquí

pool = None

def init_db():
    global pool
    if pool is None:
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
            # ssl={"ca": "/etc/ssl/certs/ca-certificates.crt"}  # descomenta si CleverCloud lo requiere
        )

def execute_read(sql: str, params=None):
    conn = pool.connection()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()
    finally:
        conn.close()

def execute_write(sql: str, params=None):
    conn = pool.connection()
    try:
        with conn.cursor() as cursor:
            affected = cursor.execute(sql, params or ())
            conn.commit()
            return affected
    finally:
        conn.close()
