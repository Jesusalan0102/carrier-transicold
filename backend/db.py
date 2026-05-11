import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 4000)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "autocommit": True,
    "cursorclass": DictCursor,
    "ssl": {
        "ca": os.path.join(os.path.dirname(__file__), "isrgrootx1.pem"),
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
    queries = [
        """CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL,
            role ENUM('admin','tecnico') DEFAULT 'tecnico'
        )""",
        """CREATE TABLE IF NOT EXISTS unidades (
            id INT AUTO_INCREMENT PRIMARY KEY,
            unit_number VARCHAR(50) UNIQUE NOT NULL,
            id_lote VARCHAR(100),
            vin_number VARCHAR(50),
            reefer_serial VARCHAR(255),
            reefer_model VARCHAR(255),
            evaporator_serial_mjs11 VARCHAR(255),
            evaporator_serial_mjd22 VARCHAR(255),
            engine_serial VARCHAR(255),
            compressor_serial VARCHAR(255),
            generator_serial VARCHAR(255),
            battery_charger_serial VARCHAR(255),
            fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS asignaciones (
            id INT AUTO_INCREMENT PRIMARY KEY,
            unidad VARCHAR(50),
            actividad_id VARCHAR(100),
            tecnico VARCHAR(100),
            estado VARCHAR(20) DEFAULT 'pendiente',
            fecha_asignacion DATETIME DEFAULT CURRENT_TIMESTAMP,
            fecha_inicio DATETIME,
            fecha_fin DATETIME,
            ticket_id INT
        )""",
        """CREATE TABLE IF NOT EXISTS evidencias (
            id INT AUTO_INCREMENT PRIMARY KEY,
            unit_number VARCHAR(50),
            nombre_archivo VARCHAR(255),
            contenido LONGBLOB,
            tecnico VARCHAR(100),
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS tickets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ticket_num INT NOT NULL UNIQUE,
            unit_number VARCHAR(50) NOT NULL,
            vin_number VARCHAR(50),
            descripcion TEXT,
            atendido BOOLEAN DEFAULT FALSE,
            reporte_enviado BOOLEAN DEFAULT FALSE,
            creado_por VARCHAR(50),
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            fecha_atencion TIMESTAMP NULL,
            fecha_reporte TIMESTAMP NULL
        )""",
        """CREATE TABLE IF NOT EXISTS inventario_data (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tabla_nombre VARCHAR(120) DEFAULT 'Principal',
            fila_idx INT NOT NULL,
            col_nombre VARCHAR(120) NOT NULL,
            valor TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS inventario_columnas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            tabla_nombre VARCHAR(120) DEFAULT 'Principal',
            col_nombre VARCHAR(120) NOT NULL,
            col_orden INT DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS toma_valores_campos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            campo_nombre VARCHAR(200) NOT NULL,
            campo_orden INT DEFAULT 0
        )""",
        """CREATE TABLE IF NOT EXISTS toma_valores_datos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            asignacion_id INT NOT NULL,
            campo_nombre VARCHAR(200) NOT NULL,
            valor TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
        )""",
        """CREATE TABLE IF NOT EXISTS comentarios_actividades (
            id INT AUTO_INCREMENT PRIMARY KEY,
            asignacion_id INT NOT NULL,
            tecnico VARCHAR(50),
            comentario TEXT,
            fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
    ]
    for q in queries:
        execute_write(q)
    # Seed admin users if not exist
    admins = execute_read("SELECT id FROM users WHERE role='admin' LIMIT 1")
    if not admins:
        execute_write(
            "INSERT IGNORE INTO users (username, password, role) VALUES (%s,%s,%s)",
            ("Ing Sepulveda", "peluche123", "admin")
        )
        execute_write(
            "INSERT IGNORE INTO users (username, password, role) VALUES (%s,%s,%s)",
            ("Admin", "admin123", "admin")
        )