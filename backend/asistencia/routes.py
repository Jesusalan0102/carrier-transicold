from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
import pymysql
from db import get_db_connection  # Asegura que apunte correctamente a tu manejador de conexiones
from datetime import datetime

# Definimos el router con el prefijo /asistencia. 
# Al incluirlo en el main bajo el prefijo /api, completará la ruta /api/asistencia
router = APIRouter(
    prefix="/asistencia",
    tags=["Asistencia"]
)

class GeofenceConfig(BaseModel):
    latitud_fija: float
    longitud_fija: float
    radio_permitido: float

@router.get("/registros")
def obtener_registros(fecha: str = Query(None)):
    """
    Obtiene y lista todos los registros de asistencia.
    Permite filtrar por fecha mediante parámetros query (?fecha=YYYY-MM-DD).
    """
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No hay conexión con la base de datos")
        
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            if fecha:
                sql = "SELECT * FROM registros_asistencia WHERE DATE(fecha) = %s ORDER BY fecha DESC"
                cursor.execute(sql, (fecha,))
            else:
                sql = "SELECT * FROM registros_asistencia ORDER BY fecha DESC"
                cursor.execute(sql)
                
            registros = cursor.fetchall()
            
            # Sanitizar objetos datetime a string para el parseo correcto de JSON en el Frontend
            for r in registros:
                if 'fecha' in r and isinstance(r['fecha'], datetime):
                    r['fecha'] = r['fecha'].strftime('%Y-%m-%d %H:%M:%S')
            return registros
            
    except Exception as e:
        print(f"Error en obtener_registros: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        connection.close()

@router.get("/configuracion")
def obtener_configuracion():
    """
    Obtiene los parámetros geográficos de la geocerca para el marcado QR.
    Si la tabla está vacía, devuelve los valores predeterminados de Tijuana por seguridad.
    """
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No hay conexión con la base de datos")
        
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT latitud_fija, longitud_fija, radio_permitido FROM configuracion_geocerca LIMIT 1")
            config = cursor.fetchone()
            if not config:
                # Valores por defecto de respaldo (vistos en tu captura de pantalla)
                return {"latitud_fija": 32.471823, "longitud_fija": -116.798104, "radio_permitido": 200.0}
            return config
    except Exception as e:
        print(f"Error en obtener_configuracion: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        connection.close()

@router.post("/configuracion")
def guardar_configuracion(config: GeofenceConfig):
    """
    Actualiza o inserta las coordenadas y radio límite permitidos para la geocerca.
    """
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No hay conexión con la base de datos")
        
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM configuracion_geocerca")
            existe = cursor.fetchone()
            count = existe[0] if isinstance(existe, tuple) else existe.get('COUNT(*)', 0)
            
            if count > 0:
                sql = """UPDATE configuracion_geocerca 
                         SET latitud_fija = %s, longitud_fija = %s, radio_permitido = %s"""
                cursor.execute(sql, (config.latitud_fija, config.longitud_fija, config.radio_permitido))
            else:
                sql = """INSERT INTO configuracion_geocerca (latitud_fija, longitud_fija, radio_permitido) 
                         VALUES (%s, %s, %s)"""
                cursor.execute(sql, (config.latitud_fija, config.longitud_fija, config.radio_permitido))
                
            connection.commit()
            return {"status": "success", "message": "Geocerca actualizada correctamente"}
    except Exception as e:
        connection.rollback()
        print(f"Error en guardar_configuracion: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        connection.close()
