"""
Respaldo manual (solo admin).

  GET  /api/respaldo/descargar            ZIP de la base de datos (sin depender de OneDrive)
  POST /api/respaldo/evidencias-ahora     fotos/videos de la DB -> OneDrive (aplicar=false = solo cuenta lo pendiente)

Sirve cuando OneDrive falla: genera el mismo ZIP que sube el respaldo nocturno (un .jsonl por tabla +
esquema.sql, sin el contenido binario de fotos/videos) y lo entrega al navegador, sin tocar OneDrive.
"""
import os
import tempfile
from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from auth import verify_token

router = APIRouter(prefix="/api/respaldo", tags=["respaldo"])


@router.get("/descargar")
def descargar_respaldo(current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    import respaldo_onedrive as rb
    tmp = tempfile.NamedTemporaryFile(prefix="respaldo_", suffix=".zip", delete=False)
    tmp.close()
    try:
        rb.generar_zip(tmp.name)
    except Exception as e:
        os.remove(tmp.name)
        raise HTTPException(status_code=500, detail=f"No se pudo generar el respaldo: {str(e)[:200]}")
    nombre = f"respaldo_{datetime.now(ZoneInfo('America/Tijuana')).strftime('%Y-%m-%d_%H%M')}.zip"
    return FileResponse(tmp.name, media_type="application/zip", filename=nombre,
                        background=BackgroundTask(os.remove, tmp.name))


@router.post("/evidencias-ahora")
def respaldar_evidencias_ahora(aplicar: bool = False, solo_videos: bool = False, unidad: str = "",
                               current_user=Depends(verify_token)):
    """Corre el respaldo de fotos/videos ya, con tope de 80 s por llamada (antes del timeout del gateway).
    Se repite hasta que `completo` sea true. Sin `aplicar=true` solo informa cuánto hay pendiente."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    import respaldo_evidencias as rev
    return rev.respaldar_evidencias(aplicar=aplicar, solo_videos=solo_videos, presupuesto_seg=80, unidad=unidad or None)
