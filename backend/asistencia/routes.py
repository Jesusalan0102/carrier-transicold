from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
import pymysql
from db import get_db_connection
from datetime import datetime

router = APIRouter(
    prefix="/asistencia",
    tags=["Asistencia"]
)

class GeofenceConfig(BaseModel):
    lat_fija: float
    lon_fija: float
    radio_metros: int

@router.get("/registros")
def obtener_registros(fecha: str = Query(None)):
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
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No hay conexión con la base de datos")
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT lat_fija, lon_fija, radio_metros FROM configuracion_geocerca LIMIT 1")
            config = cursor.fetchone()
            if not config:
                return {"lat_fija": 32.471823, "lon_fija": -116.798104, "radio_metros": 200}
            return config
    except Exception as e:
        print(f"Error en obtener_configuracion: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        connection.close()

@router.post("/configuracion")
def guardar_configuracion(config: GeofenceConfig):
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No hay conexión con la base de datos")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM configuracion_geocerca")
            resultado = cursor.fetchone()
            count = resultado.get('count', 0) if isinstance(resultado, dict) else resultado[0]
            if count > 0:
                sql = "UPDATE configuracion_geocerca SET lat_fija = %s, lon_fija = %s, radio_metros = %s"
                cursor.execute(sql, (config.lat_fija, config.lon_fija, config.radio_metros))
            else:
                sql = "INSERT INTO configuracion_geocerca (lat_fija, lon_fija, radio_metros) VALUES (%s, %s, %s)"
                cursor.execute(sql, (config.lat_fija, config.lon_fija, config.radio_metros))
            connection.commit()
            return {"status": "success", "message": "Geocerca actualizada correctamente"}
    except Exception as e:
        connection.rollback()
        print(f"Error en guardar_configuracion: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        connection.close()

@router.get("/generar-qr")
def generar_qr():
    """
    Devuelve la URL del QR de check-in y la configuración activa de geocerca.
    El frontend usa data.qr_url y data.config.{lat_fija, lon_fija, radio_metros}
    """
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No hay conexión con la base de datos")
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT lat_fija, lon_fija, radio_metros FROM configuracion_geocerca LIMIT 1")
            config = cursor.fetchone()
            if not config:
                config = {"lat_fija": 32.471823, "lon_fija": -116.798104, "radio_metros": 200}

        # La URL que el técnico escaneará para hacer check-in
        import os
        base_url = os.getenv("APP_BASE_URL", "").rstrip("/")
        qr_url = f"{base_url}/app/checkin"

        return {
            "qr_url": qr_url,
            "config": config
        }
    except Exception as e:
        print(f"Error en generar_qr: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        connection.close()
