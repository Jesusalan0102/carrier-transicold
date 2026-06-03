# backend/db.py
import pymysql
from DBUtils.PooledDB import PooledDB
import os

# Pool de conexiones
pool = None

def init_db():
    global pool
    pool = PooledDB(
        creator=pymysql,
        maxconnections=10,
        mincached=2,
        maxcached=5,
        blocking=True,
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 4000)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        charset='utf8mb4',
        ssl={"ca": "/etc/ssl/certs/ca-certificates.crt"}
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
            cursor.execute(sql, params or ())
            conn.commit()
            return cursor.rowcount
    finally:
        conn.close()
