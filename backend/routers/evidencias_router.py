from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from auth import verify_token
from db import execute_read, execute_write
from typing import List
import zipfile
import io
import logging

# ── Importación opcional de OneDrive ────────────────────────────────────────
# Si las variables MS_* no están configuradas, la app sigue funcionando normal
try:
    from onedrive_service import sync_evidencia, sync_zip_evidencias
    ONEDRIVE_ENABLED = True
except ImportError:
    ONEDRIVE_ENABLED = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/evidencias", tags=["evidencias"])

MAX_FOTOS = 100


# ── CONTAR FOTOS DE UNA UNIDAD/TÉCNICO ────────────────────────────────────
@router.get("/count")
def contar_evidencias(unit_number: str, tecnico: str, current_user=Depends(verify_token)):
    res = execute_read(
        "SELECT COUNT(*) AS total FROM evidencias WHERE unit_number=%s AND tecnico=%s",
        (unit_number, tecnico)
    )
    return {"total": res[0]["total"] if res else 0}


# ── TOTAL DE FOTOS POR UNIDAD ──────────────────────────────────────────────
@router.get("/total/{unit_number}")
def total_por_unidad(unit_number: str, current_user=Depends(verify_token)):
    res = execute_read(
        "SELECT COUNT(*) AS total FROM evidencias WHERE unit_number=%s", (unit_number,)
    )
    return {"total": res[0]["total"] if res else 0}


# ── SUBIR FOTOS ────────────────────────────────────────────────────────────
@router.post("/upload")
async def subir_evidencias(
    unidad: str = Form(...),
    tecnico: str = Form(...),
    files: List[UploadFile] = File(...),
    current_user=Depends(verify_token)
):
    # Verificar límite
    res = execute_read(
        "SELECT COUNT(*) AS total FROM evidencias WHERE unit_number=%s AND tecnico=%s",
        (unidad, tecnico)
    )
    ya_guardadas = res[0]["total"] if res else 0
    disponibles  = MAX_FOTOS - ya_guardadas
    if disponibles <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"Ya alcanzaste el límite de {MAX_FOTOS} fotos"
        )

    files_a_guardar = files[:disponibles]
    guardadas        = 0
    subidas_onedrive = 0

    for file in files_a_guardar:
        contenido = await file.read()

        # 1. Guardar en TiDB (comportamiento original sin cambios)
        ok = execute_write(
            "INSERT INTO evidencias (unit_number, nombre_archivo, contenido, tecnico) VALUES (%s,%s,%s,%s)",
            (unidad, file.filename, contenido, tecnico)
        )
        if ok:
            guardadas += 1

            # 2. Sincronizar con OneDrive automáticamente
            if ONEDRIVE_ENABLED:
                try:
                    sync_evidencia(unidad, file.filename, contenido)
                    subidas_onedrive += 1
                except Exception as e:
                    # No fallar si OneDrive falla — TiDB ya tiene la foto
                    logger.warning(f"[OneDrive] No se pudo subir {file.filename}: {e}")

    respuesta = {
        "mensaje": f"{guardadas} foto(s) guardada(s)",
        "guardadas": guardadas,
    }
    if ONEDRIVE_ENABLED:
        respuesta["onedrive"] = f"{subidas_onedrive}/{guardadas} foto(s) sincronizadas con OneDrive"

    return respuesta


# ── DESCARGAR ZIP DE TODAS LAS FOTOS DE UNA UNIDAD ────────────────────────
@router.get("/download/{unit_number}")
def descargar_evidencias(unit_number: str, current_user=Depends(verify_token)):
    meta = execute_read(
        "SELECT id, nombre_archivo FROM evidencias WHERE unit_number=%s",
        (unit_number,)
    )
    if not meta:
        raise HTTPException(status_code=404, detail="No hay evidencias para esta unidad")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
        nombres_vistos = {}
        for m in meta:
            fila = execute_read("SELECT contenido FROM evidencias WHERE id=%s", (m["id"],))
            if not fila or not fila[0]["contenido"]:
                continue
            nombre = m["nombre_archivo"] or f"foto_{m['id']}.jpg"
            if nombre in nombres_vistos:
                nombres_vistos[nombre] += 1
                partes = nombre.rsplit(".", 1)
                nombre = (
                    f"{partes[0]}_{nombres_vistos[nombre]}.{partes[1]}"
                    if len(partes) == 2
                    else f"{nombre}_{nombres_vistos[nombre]}"
                )
            else:
                nombres_vistos[nombre] = 0
            zf.writestr(nombre, fila[0]["contenido"])

    buf.seek(0)
    zip_bytes = buf.getvalue()

    # Sincronizar ZIP con OneDrive en background (no bloquea la descarga)
    if ONEDRIVE_ENABLED:
        try:
            sync_zip_evidencias(unit_number, zip_bytes)
        except Exception as e:
            logger.warning(f"[OneDrive] No se pudo subir ZIP de {unit_number}: {e}")

    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={unit_number}_evidencias.zip",
            "Cache-Control": "no-store",
        }
    )


# ── SINCRONIZAR TODAS LAS EVIDENCIAS DE UNA UNIDAD A ONEDRIVE ─────────────
# Endpoint manual para migrar fotos históricas que ya estaban en TiDB
@router.post("/sync-onedrive/{unit_number}")
def sync_unidad_onedrive(unit_number: str, current_user=Depends(verify_token)):
    """
    Sube a OneDrive todas las fotos de una unidad que ya están en TiDB.
    Útil para migrar el historial existente.
    """
    if not ONEDRIVE_ENABLED:
        raise HTTPException(status_code=503, detail="OneDrive no está configurado")

    meta = execute_read(
        "SELECT id, nombre_archivo FROM evidencias WHERE unit_number=%s",
        (unit_number,)
    )
    if not meta:
        raise HTTPException(status_code=404, detail="No hay evidencias para esta unidad")

    subidas = 0
    errores = 0
    for m in meta:
        fila = execute_read("SELECT contenido FROM evidencias WHERE id=%s", (m["id"],))
        if not fila or not fila[0]["contenido"]:
            continue
        try:
            sync_evidencia(unit_number, m["nombre_archivo"] or f"foto_{m['id']}.jpg", fila[0]["contenido"])
            subidas += 1
        except Exception as e:
            logger.error(f"[OneDrive] Error en foto id={m['id']}: {e}")
            errores += 1

    return {
        "mensaje": f"Sincronización completada para {unit_number}",
        "subidas": subidas,
        "errores": errores,
    }
