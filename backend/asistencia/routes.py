"""
routes.py — Backend de Asistencia Carrier Transicold
Versión actualizada con Timezone Tijuana correcto y endpoints mejorados.
"""

from fastapi import APIRouter, HTTPException, Query, status, Depends, Form, File, UploadFile
from pydantic import BaseModel
from typing import Optional
import pymysql
from db import get_db_connection
from datetime import datetime
import zoneinfo
import os
import math
import base64
from auth import verify_token

# ====================== TIMEZONE TIJUANA ======================
TZ_TJ = zoneinfo.ZoneInfo("America/Tijuana")

router = APIRouter(
    prefix="/asistencia",
    tags=["Asistencia"]
)


class GeofenceConfig(BaseModel):
    lat_fija: float
    lon_fija: float
    radio_metros: int

class RegistroAsistenciaBody(BaseModel):
    tipo: str
    lat: float
    lon: float
    accuracy: Optional[float] = None
    foto_base64: Optional[str] = None


# ── GET Registros ─────────────────────────────────────────────────────────────
@router.get("/registros")
def obtener_registros(fecha: str = Query(None)):
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="No hay conexión con la base de datos")
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            if fecha:
                cursor.execute(
                    "SELECT * FROM registros_asistencia WHERE DATE(fecha) = %s ORDER BY fecha DESC, hora_checkin DESC", 
                    (fecha,)
                )
            else:
                cursor.execute("SELECT * FROM registros_asistencia ORDER BY fecha DESC, hora_checkin DESC")
            
            registros = cursor.fetchall()
            result = []
            for r in registros:
                row = dict(r)
                if 'fecha' in row and isinstance(row['fecha'], datetime):
                    row['fecha'] = row['fecha'].strftime('%Y-%m-%d')
                if 'hora_checkin' in row and row['hora_checkin']:
                    row['hora_checkin'] = str(row['hora_checkin'])[:8]
                row.pop('foto', None)
                result.append(row)
            return result
    except Exception as e:
        print(f"Error en obtener_registros: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


# ── Configuración Geocerca ────────────────────────────────────────────────────
@router.get("/configuracion")
def obtener_configuracion():
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="No hay conexión con la base de datos")
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT lat_fija, lon_fija, radio_metros FROM configuracion_geocerca LIMIT 1")
            config = cursor.fetchone()
            if not config:
                return {"lat_fija": 32.471823, "lon_fija": -116.798104, "radio_metros": 200}
            return config
    except Exception as e:
        print(f"Error en obtener_configuracion: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


@router.post("/configuracion")
def guardar_configuracion(config: GeofenceConfig):
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="No hay conexión con la base de datos")
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
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()


# ── REGISTRO DE ASISTENCIA (CORREGIDO CON TZ TIJUANA) ────────────────────────
def _haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


@router.post("/registrar")
async def registrar_asistencia(
    body: RegistroAsistenciaBody,
    current_user=Depends(verify_token)
):
    """Registra entrada/salida con hora exacta de Tijuana"""
    username = current_user["username"]
    tipo = body.tipo
    lat = body.lat
    lon = body.lon

    if tipo not in ("entrada", "salida"):
        raise HTTPException(400, "Tipo debe ser 'entrada' o 'salida'")

    now_tj = datetime.now(TZ_TJ)
    fecha_hoy = now_tj.date().isoformat()
    hora_actual = now_tj.strftime("%H:%M:%S")

    # Obtener configuración de geocerca
    config = obtener_configuracion()
    distancia = _haversine(lat, lon, config["lat_fija"], config["lon_fija"])
    aprobado = 1 if distancia <= config["radio_metros"] else 0

    # Procesar foto base64 si viene
    foto_bytes = None
    if body.foto_base64:
        try:
            b64data = body.foto_base64.split(",", 1)[-1]
            foto_bytes = base64.b64decode(b64data)
        except Exception:
            foto_bytes = None

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO registros_asistencia 
                (username, fecha, tipo, hora_checkin, latitud, longitud, distancia_metros, aprobado, foto)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (username, fecha_hoy, tipo, hora_actual, lat, lon, round(distancia), aprobado, foto_bytes)
            )
            connection.commit()

        return {
            "ok": True,
            "aprobado": bool(aprobado),
            "distancia_metros": round(distancia),
            "radio_metros": config["radio_metros"],
            "hora": hora_actual,
            "fecha": fecha_hoy,
            "tipo": tipo,
            "mensaje": "✅ Registro exitoso" if aprobado else f"❌ Fuera del perímetro ({round(distancia)}m)"
        }

    except Exception as e:
        print(f"Error registrando asistencia: {e}")
        raise HTTPException(500, str(e))
    finally:
        connection.close()


# ── QR y otras utilidades ─────────────────────────────────────────────────────
@router.get("/generar-qr")
def generar_qr():
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="No hay conexión con la base de datos")
    try:
        with connection.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute("SELECT lat_fija, lon_fija, radio_metros FROM configuracion_geocerca LIMIT 1")
            config = cursor.fetchone() or {"lat_fija": 32.471823, "lon_fija": -116.798104, "radio_metros": 200}
        
        base_url = os.getenv("APP_BASE_URL", "").rstrip("/")
        qr_url = f"{base_url}/app/checkin"
        return {"qr_url": qr_url, "config": config}
    except Exception as e:
        print(f"Error en generar_qr: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        connection.close()
