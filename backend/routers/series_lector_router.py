"""
series_lector_router.py
-----------------------
POST /api/series/leer-foto   -> recibe la foto de una etiqueta y devuelve las series que se leyeron.
GET  /api/series/lector-estado -> qué motores de lectura están instalados en este servidor.

El endpoint solo LEE: no guarda nada. El técnico revisa y confirma los datos en la pantalla de
Toma de Series, y ahí se guardan con el flujo normal (PUT /api/unidades/series/update).
"""
import asyncio
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from PIL import UnidentifiedImageError

import series_lector
from auth import verify_token

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/series", tags=["series-lector"])

MAX_BYTES = 15 * 1024 * 1024
_en_cola = asyncio.Semaphore(4)       # a lo más 4 fotos esperando/procesándose a la vez


@router.get("/lector-estado")
def lector_estado(current_user: dict = Depends(verify_token)):
    return series_lector.estado_motores()


@router.post("/leer-foto")
async def leer_foto(archivo: UploadFile = File(...), current_user: dict = Depends(verify_token)):
    tipo = (archivo.content_type or "").lower()
    if tipo and not tipo.startswith("image/"):
        raise HTTPException(status_code=415, detail="El archivo debe ser una imagen.")
    datos = await archivo.read(MAX_BYTES + 1)
    if not datos:
        raise HTTPException(status_code=400, detail="La imagen llegó vacía.")
    if len(datos) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="La imagen pesa más de 15 MB.")

    if _en_cola.locked():
        raise HTTPException(status_code=429, detail="El lector está ocupado; intenta de nuevo en unos segundos.")
    async with _en_cola:
        try:
            return await run_in_threadpool(series_lector.leer_etiqueta, datos)
        except HTTPException:
            raise
        except (UnidentifiedImageError, OSError) as e:      # archivo dañado o formato no soportado
            logger.warning(f"[series-lector] imagen ilegible de {current_user.get('username')}: {e}")
            raise HTTPException(status_code=422,
                                detail="No se pudo abrir la imagen. Toma la foto de nuevo (JPG o PNG).")
        except Exception as e:
            logger.exception(f"[series-lector] error leyendo foto de {current_user.get('username')}: {e}")
            raise HTTPException(status_code=422,
                                detail="No se pudo abrir la imagen. Toma la foto de nuevo (JPG o PNG).")
