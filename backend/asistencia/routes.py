from fastapi import APIRouter, HTTPException, Query, status, Depends
from pydantic import BaseModel
from typing import Optional
import pymysql
from db import get_db_connection
from datetime import datetime
import os
import math
from auth import verify_token

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
                cursor.execute("SELECT * FROM registros_asistencia WHERE DATE(fecha) = %s ORDER BY fecha DESC", (fecha,))
            else:
                cursor.execute("SELECT * FROM registros_asistencia ORDER BY fecha DESC")
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
                cursor.execute(
                    "UPDATE configuracion_geocerca SET lat_fija = %s, lon_fija = %s, radio_metros = %s",
                    (config.lat_fija, config.lon_fija, config.radio_metros)
                )
            else:
                cursor.execute(
                    "INSERT INTO configuracion_geocerca (lat_fija, lon_fija, radio_metros) VALUES (%s, %s, %s)",
                    (config.lat_fija, config.lon_fija, config.radio_metros)
                )
            connection.commit()
            return {"status": "success", "message": "Geocerca actualizada correctamente"}
    except Exception as e:
        connection.rollback()
        print(f"Error en guardar_configuracion: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        connection.close()

class RegistroCheckin(BaseModel):
    tipo:       str            # 'entrada' | 'salida'
    lat:        float
    lon:        float
    accuracy:   Optional[float] = None
    foto_base64: Optional[str] = None   # jpeg base64 de la foto de validación

def _haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

@router.post("/registrar")
def registrar_checkin(payload: RegistroCheckin, current_user=Depends(verify_token)):
    if payload.tipo not in ("entrada", "salida"):
        raise HTTPException(status_code=400, detail="tipo debe ser 'entrada' o 'salida'")

    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Sin conexión a base de datos")
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT lat_fija, lon_fija, radio_metros FROM configuracion_geocerca LIMIT 1")
            cfg = cursor.fetchone() or {"lat_fija": 32.471823, "lon_fija": -116.798104, "radio_metros": 200}

        distancia = _haversine(payload.lat, payload.lon, cfg["lat_fija"], cfg["lon_fija"])
        aprobado  = 1 if distancia <= cfg["radio_metros"] else 0
        ahora     = datetime.now()
        hora_str  = ahora.strftime("%H:%M:%S")

        foto_bytes = None
        if payload.foto_base64:
            import base64
            try:
                header, _, data = payload.foto_base64.partition(',')
                foto_bytes = base64.b64decode(data if data else header)
            except Exception:
                foto_bytes = None

        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO registros_asistencia "
                "(username, fecha, tipo, hora_checkin, distancia_metros, aprobado, foto) "
                "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                (current_user["username"], ahora, payload.tipo, hora_str, round(distancia, 1), aprobado, foto_bytes)
            )
        connection.commit()

        return {
            "ok":       True,
            "aprobado": bool(aprobado),
            "distancia_metros": round(distancia, 1),
            "radio_metros":     cfg["radio_metros"],
            "hora":     hora_str,
            "tipo":     payload.tipo,
            "mensaje":  "✅ Registro aprobado" if aprobado else f"❌ Fuera del perímetro ({round(distancia)}m / límite {cfg['radio_metros']}m)"
        }
    except Exception as e:
        connection.rollback()
        print(f"Error en registrar_checkin: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


@router.get("/generar-qr")
def generar_qr():
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="No hay conexión con la base de datos")
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT lat_fija, lon_fija, radio_metros FROM configuracion_geocerca LIMIT 1")
            config = cursor.fetchone()
            if not config:
                config = {"lat_fija": 32.471823, "lon_fija": -116.798104, "radio_metros": 200}
        base_url = os.getenv("APP_BASE_URL", "").rstrip("/")
        qr_url = f"{base_url}/app/checkin"
        return {"qr_url": qr_url, "config": config}
    except Exception as e:
        print(f"Error en generar_qr: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    finally:
        connection.close()
