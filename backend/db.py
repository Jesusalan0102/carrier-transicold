# db.py
import sqlite3
import os
import hashlib

DB_PATH = os.getenv("DATABASE_URL", "carrier.db")
if DB_PATH.startswith("sqlite:///"):
    DB_PATH = DB_PATH.replace("sqlite:///", "")

def get_db_connection():
    """Retorna una conexión a la base de datos SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa la base de datos con todas las tablas necesarias"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # ========== TABLAS EXISTENTES ==========
    
    # Tabla de usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'tecnico'
        )
    ''')
    
    # Tabla de unidades
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS unidades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_number TEXT UNIQUE NOT NULL,
            id_lote TEXT,
            vin_number TEXT,
            reefer_serial TEXT,
            reefer_model TEXT,
            evaporator_serial_mjs11 TEXT,
            evaporator_serial_mjd22 TEXT,
            engine_serial TEXT,
            compressor_serial TEXT,
            generator_serial TEXT,
            battery_charger_serial TEXT
        )
    ''')
    
    # Tabla de asignaciones
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS asignaciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unidad TEXT NOT NULL,
            tecnico TEXT NOT NULL,
            actividad_id TEXT NOT NULL,
            estado TEXT DEFAULT 'pendiente',
            comentario TEXT,
            fecha_asignacion TEXT DEFAULT CURRENT_TIMESTAMP,
            fecha_completado TEXT,
            FOREIGN KEY (tecnico) REFERENCES usuarios(username)
        )
    ''')
    
    # Tabla de tickets
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_num TEXT UNIQUE NOT NULL,
            unit_number TEXT NOT NULL,
            vin_number TEXT,
            descripcion TEXT NOT NULL,
            creado_por TEXT NOT NULL,
            tecnico_asignado TEXT NOT NULL,
            atendido INTEGER DEFAULT 0,
            reporte_enviado INTEGER DEFAULT 0,
            reporte_texto TEXT,
            fecha_creacion TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de inventario config
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventario_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            columnas TEXT
        )
    ''')
    
    # Tabla de inventario datos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventario_datos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            datos TEXT
        )
    ''')
    
    # Tabla de toma de valores campos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS toma_valores_campos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campo_nombre TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Tabla de toma de valores registros
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS toma_valores_registros (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asignacion_id INTEGER NOT NULL,
            valores TEXT NOT NULL,
            fecha_registro TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de evidencias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evidencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unit_number TEXT NOT NULL,
            tecnico TEXT NOT NULL,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            fecha_subida TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla de comentarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comentarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            asignacion_id INTEGER NOT NULL,
            usuario TEXT NOT NULL,
            comentario TEXT NOT NULL,
            fecha TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ========== TABLAS NUEVAS DE ASISTENCIA ==========
    
    # Tabla de horarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS horarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            fecha TEXT NOT NULL,
            semana TEXT NOT NULL,
            hora_entrada TEXT,
            hora_salida TEXT,
            UNIQUE(username, fecha)
        )
    ''')
    
    # Tabla de asistencia
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS asistencia (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            fecha TEXT NOT NULL,
            hora TEXT NOT NULL,
            lat_fija REAL NOT NULL,
            lon_fija REAL NOT NULL,
            radio_metros INTEGER NOT NULL,
            lat_tecnico REAL NOT NULL,
            lon_tecnico REAL NOT NULL,
            distancia_m REAL NOT NULL,
            gps_accuracy REAL,
            selfie_path TEXT,
            dentro_radio INTEGER DEFAULT 0,
            fecha_registro TEXT NOT NULL
        )
    ''')
    
    # Crear usuario admin por defecto si no existe
    cursor.execute("SELECT * FROM usuarios WHERE username = 'admin'")
    if not cursor.fetchone():
        admin_pass = hashlib.sha256("admin123".encode()).hexdigest()
        cursor.execute("INSERT INTO usuarios (username, password, role) VALUES (?, ?, ?)",
                       ("admin", admin_pass, "admin"))
    
    # Insertar actividades por defecto si no existen (opcional)
    actividades_default = [
        'Cableado', 'Programación', 'Soldadura', 'Check de fugas', 'Vacío',
        'Cerrado', 'Pre-viaje', 'Horas Corridas', 'Standby', 'GPS',
        'Corriendo', 'Inspección', 'Accesorios', 'Toma de Valores',
        'Evidencia', 'Toma de Series'
    ]
    
    conn.commit()
    conn.close()
    
    print("✅ Base de datos inicializada correctamente")
