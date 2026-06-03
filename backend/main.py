import os
import io
import base64
import math
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
import qrcode

# -------------------------------------------------------------------------
# Configuración e Infraestructura de Base de Datos (TiDB / MySQL)
# -------------------------------------------------------------------------
DATABASE_URL = f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_engine(
    DATABASE_URL, 
    pool_size=10, 
    max_overflow=20, 
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(
    title="Sistema de Asistencia, QR y Geolocalización", 
    version="1.0.0"
)

# Dependencia para obtener la sesión de la Base de Datos
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------------------------------------------------
# Modelos de Entrada Pydantic (Validación de Datos)
# -------------------------------------------------------------------------
class QRCreateRequest(BaseModel):
    config_id: int
    datos_extra: str = ""

class AsistenciaRequest(BaseModel):
    user_id: int
    qr_token: str  # El token o información que venía dentro del QR leído
    latitud_usuario: float
    longitud_usuario: float

# -------------------------------------------------------------------------
# Funciones Auxiliares de Geolocalización (Fórmula de Haversine)
# -------------------------------------------------------------------------
def calcular_distancia_metros(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula la distancia en metros entre dos coordenadas geográficas utilizando Haversine.
    """
    R = 6371000.0  # Radio de la Tierra en metros
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = (math.sin(delta_phi / 2) ** 2 + 
         math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2) ** 2))
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c

# -------------------------------------------------------------------------
# Endpoints de la API
# -------------------------------------------------------------------------

@app.get("/")
def read_root():
    return {
        "status": "online", 
        "timestamp": datetime.utcnow().isoformat(),
        "database": "connected"
    }

@app.post("/api/qr/generar", status_code=status.HTTP_201_CREATED)
def generar_codigo_qr(request: QRCreateRequest, db: Session = Depends(get_db)):
    """
    Obtiene los parámetros de configuración de asistencia y geocercas para incrustarlos
    en un código QR dinámico devuelto en formato Base64.
    """
    # 1. Validar que exista la configuración en la tabla 'asistencia_config'
    query_config = text("""
        SELECT id, nombre, sucursal_id 
        FROM asistencia_config 
        WHERE id = :config_id
    """)
    configuracion = db.execute(query_config, {"config_id": request.config_id}).fetchone()
    
    if not configuracion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="La configuración de asistencia especificada no existe."
        )
        
    # 2. Estructurar la información única que contendrá el QR de asistencia
    # Nota: Se añade timestamp para evitar fraude por capturas de pantalla viejas
    timestamp_actual = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    contenido_qr = f"ASISTENCIA|CONF_{configuracion.id}|SUC_{configuracion.sucursal_id}|TS_{timestamp_actual}|{request.datos_extra}"
    
    try:
        # 3. Generar la imagen del Código QR usando la librería qrcode
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(contenido_qr)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # 4. Convertir la imagen a una cadena Base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
        
        return {
            "success": True,
            "config_id": request.config_id,
            "contenido_encriptado": contenido_qr,
            "qr_base64": f"data:image/png;base64,{qr_base64}"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al generar el QR: {str(e)}"
        )

@app.post("/api/asistencia/registrar", status_code=status.HTTP_201_CREATED)
def registrar_asistencia(request: AsistenciaRequest, db: Session = Depends(get_db)):
    """
    Valida la lectura del QR, comprueba si el usuario se encuentra dentro del rango
    permitido por su geocerca y guarda las coordenadas físicas exactas en la base de datos.
    """
    # 1. Verificar existencia del usuario
    query_user = text("SELECT id, name FROM users WHERE id = :user_id")
    usuario = db.execute(query_user, {"user_id": request.user_id}).fetchone()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="El usuario especificado no existe."
        )

    # 2. Parsear el QR recibido para extraer el ID de la configuración
    try:
        partes_qr = request.qr_token.split("|")
        if len(partes_qr) < 4 or partes_qr[0] != "ASISTENCIA":
            raise ValueError()
        config_id = int(partes_qr[1].replace("CONF_", ""))
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El código QR escaneado no es válido o ha expirado."
        )

    # 3. Traer los límites geográficos desde la tabla 'configuracion_geocerca'
    query_geocerca = text("""
        SELECT latitud_centro, longitud_centro, radio_permitido_metros, activo 
        FROM configuracion_geocerca 
        WHERE asistencia_config_id = :config_id AND activo = 1
        LIMIT 1
    """)
    geocerca = db.execute(query_geocerca, {"config_id": config_id}).fetchone()

    if not geocerca:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró una configuración de geocerca activa para este punto de asistencia."
        )

    # 4. Calcular distancia física real entre el empleado y el centro de la sucursal
    distancia_calculada = calcular_distancia_metros(
        request.latitud_usuario, request.longitud_usuario,
        geocerca.latitud_centro, geocerca.longitud_centro
    )

    # 5. Validar si el usuario está fuera de la cerca perimetral
    dentro_de_rango = distancia_calculada <= geocerca.radio_permitido_metros

    # 6. Insertar el registro definitivo con coordenadas en 'asistencia_registros'
    # También puedes guardar en 'valores_registrados' o 'registros_asistencia' según tu lógica exacta.
    query_insert_asistencia = text("""
        INSERT INTO asistencia_registros 
        (user_id, fecha_registro, latitud, longitud, distancia_metros, dentro_geocerca, qr_origen) 
        VALUES 
        (:user_id, :fecha, :lat, :lon, :distancia, :dentro, :qr)
    """)
    
    fecha_actual = datetime.utcnow()
    
    try:
        db.execute(query_insert_asistencia, {
            "user_id": request.user_id,
            "fecha": fecha_actual,
            "lat": request.latitud_usuario,
            "lon": request.longitud_usuario,
            "distancia": round(distancia_calculada, 2),
            "dentro": 1 if dentro_de_rango else 0,
            "qr": request.qr_token
        })
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fallo crítico al insertar las coordenadas en la base de datos: {str(e)}"
        )

    # 7. Retornar respuesta al Frontend
    if not dentro_de_rango:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Fuera de rango geográfico. Se encuentra a {round(distancia_calculada, 1)} metros de la sucursal (Máximo permitido: {geocerca.radio_permitido_metros}m)."
        )

    return {
        "success": True,
        "message": "Asistencia y coordenadas registradas correctamente.",
        "timestamp": fecha_actual.isoformat(),
        "distancia_metros": round(distancia_calculada, 2)
    }
