# BUSCA LA FUNCIÓN QUE CARGA LA CONFIGURACIÓN Y REEMPLÁZALA POR ESTA VERSIÓN COMPLETA:
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import pymysql
from database import get_db_connection  # Asegúrate de que esta importación sea correcta según tu estructura
from datetime import datetime

router = APIRouter()

class GeofenceConfig(BaseModel):
    latitud_fija: float
    longitud_fija: float
    radio_permitido: float

@router.get("/registros")
def obtener_registros(fecha: str = Query(None)):
    """Obtiene los registros de asistencia filtrados por fecha"""
    connection = get_db_connection()  # CORREGIDO: Se agregaron los paréntesis ()
    if not connection:
        raise HTTPException(status_code=500, detail="Error de conexión con la base de datos")
    
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            if fecha:
                sql = "SELECT * FROM registros_asistencia WHERE DATE(fecha) = %s ORDER BY fecha DESC"
                cursor.execute(sql, (fecha,))
            else:
                sql = "SELECT * FROM registros_asistencia ORDER BY fecha DESC"
                cursor.execute(sql)
            
            registros = cursor.fetchall()
            
            # Formatear objetos datetime a string para evitar errores de serialización JSON
            for r in registros:
                if 'fecha' in r and isinstance(r['fecha'], datetime):
                    r['fecha'] = r['fecha'].strftime('%Y-%m-%d %H:%M:%S')
                    
            return registros
    except Exception as e:
        print(f"Error en obtener_registros: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()

@router.get("/configuracion")
def obtener_configuracion():
    """Obtiene la configuración actual de la geocerca"""
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Error de conexión")
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT latitud_fija, longitud_fija, radio_permitido FROM configuracion_geocerca LIMIT 1")
            config = cursor.fetchone()
            if not config:
                return {"latitud_fija": 32.471823, "longitud_fija": -116.798104, "radio_permitido": 200.0}
            return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()

@router.post("/configuracion")
def guardar_configuracion(config: GeofenceConfig):
    """Guarda o actualiza la configuración de la geocerca"""
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Error de conexión")
    try:
        with connection.cursor() as cursor:
            # Verificar si ya existe un registro
            cursor.execute("SELECT COUNT(*) FROM configuracion_geocerca")
            existe = cursor.fetchone()[0]
            
            if existe > 0:
                sql = """UPDATE configuracion_geocerca 
                         SET latitud_fija = %s, longitud_fija = %s, radio_permitido = %s"""
                cursor.execute(sql, (config.latitud_fija, config.longitud_fija, config.radio_permitido))
            else:
                sql = """INSERT INTO configuracion_geocerca (latitud_fija, longitud_fija, radio_permitido) 
                         VALUES (%s, %s, %s)"""
                cursor.execute(sql, (config.latitud_fija, config.longitud_fija, config.radio_permitido))
                
            connection.commit()
            return {"status": "success", "message": "Configuración guardada correctamente"}
    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()
