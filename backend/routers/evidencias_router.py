from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from auth import verify_token
from db import execute_read, execute_write
from typing import List
import zipfile
import io
import logging

# ── Importación opcional de OneDrive ────────────────────────────────────────
try:
    from onedrive_service import sync_evidencias_lote, sync_zip_evidencias
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
    background_tasks: BackgroundTasks,          # NUEVO: para subir a OneDrive en background
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

    # FIX: Leer todos los archivos primero y guardar en TiDB
    # Antes: se leía y subía a OneDrive dentro del mismo loop → bloqueaba la respuesta
    archivos_para_onedrive = []  # acumular para subir en lote después

    for file in files_a_guardar:
        contenido = await file.read()

        ok = execute_write(
            "INSERT INTO evidencias (unit_number, nombre_archivo, contenido, tecnico) VALUES (%s,%s,%s,%s)",
            (unidad, file.filename, contenido, tecnico)
        )
        if ok:
            guardadas += 1
            # Acumular para subida en lote a OneDrive
            if ONEDRIVE_ENABLED:
                archivos_para_onedrive.append((file.filename, contenido))

    # FIX: Subir a OneDrive en background (no bloquea la respuesta al usuario)
    # Antes: la respuesta tardaba porque esperaba que terminara cada subida a OneDrive
    # Ahora: TiDB responde al usuario de inmediato y OneDrive se sincroniza en paralelo
    if ONEDRIVE_ENABLED and archivos_para_onedrive:
        background_tasks.add_task(
            _sync_lote_background, unidad, archivos_para_onedrive
        )

    return {
        "mensaje":  f"{guardadas} foto(s) guardada(s)",
        "guardadas": guardadas,
        "onedrive": f"Sincronizando {len(archivos_para_onedrive)} foto(s) en segundo plano..." if ONEDRIVE_ENABLED else "OneDrive no configurado",
    }


def _sync_lote_background(unidad: str, archivos: list):
    """
    Tarea de background: sube todas las fotos a OneDrive en paralelo.
    Si alguna falla, reintenta automáticamente (ver onedrive_service._upload_with_retry).
    """
    try:
        resultado = sync_evidencias_lote(unidad, archivos, max_workers=4)
        logger.info(
            f"[OneDrive] Lote {unidad}: "
            f"{len(resultado['subidas'])} subidas, "
            f"{len(resultado['errores'])} errores"
        )
        if resultado["errores"]:
            for err in resultado["errores"]:
                logger.error(f"[OneDrive] Falló {err['archivo']}: {err['error']}")
    except Exception as e:
        logger.error(f"[OneDrive] Error en sync background para {unidad}: {e}")


# ── DESCARGAR ZIP DE TODAS LAS FOTOS DE UNA UNIDAD ────────────────────────
@router.get("/download/{unit_number}")
def descargar_evidencias(unit_number: str, background_tasks: BackgroundTasks, current_user=Depends(verify_token)):
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
        background_tasks.add_task(sync_zip_evidencias, unit_number, zip_bytes)

    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename={unit_number}_evidencias.zip",
            "Cache-Control": "no-store",
        }
    )


# ── SINCRONIZAR TODAS LAS EVIDENCIAS DE UNA UNIDAD A ONEDRIVE ─────────────
@router.post("/sync-onedrive/{unit_number}")
def sync_unidad_onedrive(unit_number: str, background_tasks: BackgroundTasks, current_user=Depends(verify_token)):
    """
    Sube a OneDrive todas las fotos de una unidad que ya están en TiDB.
    Útil para migrar el historial existente.
    Ahora corre en background: responde de inmediato y sincroniza en paralelo.
    """
    if not ONEDRIVE_ENABLED:
        raise HTTPException(status_code=503, detail="OneDrive no está configurado")

    meta = execute_read(
        "SELECT id, nombre_archivo, contenido FROM evidencias WHERE unit_number=%s",
        (unit_number,)
    )
    if not meta:
        raise HTTPException(status_code=404, detail="No hay evidencias para esta unidad")

    archivos = [
        (m["nombre_archivo"] or f"foto_{m['id']}.jpg", m["contenido"])
        for m in meta
        if m.get("contenido")
    ]

    background_tasks.add_task(_sync_lote_background, unit_number, archivos)

    return {
        "mensaje":  f"Sincronización iniciada para {unit_number}",
        "total":    len(archivos),
        "estado":   "Corriendo en segundo plano (revisa logs para resultado)",
    }
