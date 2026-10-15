from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Header
from fastapi.responses import StreamingResponse, Response, FileResponse
from starlette.background import BackgroundTask
from fastapi.concurrency import run_in_threadpool
from auth import verify_token
from db import execute_read, execute_write, execute_write_with_id
import evidencia_partes as ep
from typing import List, Optional
import zipfile
import io
import os
import csv
import tempfile
import logging
import asyncio
import re
import time
import uuid
import requests
from PIL import Image


def require_admin_or_visor(current_user=Depends(verify_token)):
    if current_user["role"] not in ("admin", "visor", "lider"):
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores, visores y líderes")
    return current_user

# ── Importación opcional de OneDrive ────────────────────────────────────────
try:
    from onedrive_service import sync_evidencia, sync_zip_evidencias, sync_video_evidencia, download_item_bytes, get_download_url
    ONEDRIVE_ENABLED = True
except ImportError:
    ONEDRIVE_ENABLED = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/evidencias", tags=["evidencias"])

MAX_FOTOS        = 100
MAX_DIMENSION    = 1280          # px — lado más largo
JPEG_QUALITY     = 72            # 0-95; 72 es un buen balance calidad/tamaño
MAX_BYTES_BEFORE = 800_000       # solo comprimir si pesa más de 800 KB
MAX_CONCURRENT   = 5             # fotos que se procesan en paralelo a la vez
MAX_CONCURRENT_VIDEO = 1         # videos a la vez (cada uno puede pesar hasta 80MB en RAM)

# ── Video ───────────────────────────────────────────────────────────────
VIDEO_EXTENSIONS = {"mp4", "mov", "webm", "m4v", "3gp", "avi", "mkv"}
IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp", "heic", "heif"}
MAX_VIDEO_BYTES  = 80 * 1024 * 1024   # 80 MB por video — suficiente para clips
                                       # cortos de celular sin arriesgar la DB
MIME_MAP = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
    "gif": "image/gif", "webp": "image/webp", "heic": "image/heic", "heif": "image/heif",
    "mp4": "video/mp4", "mov": "video/quicktime", "webm": "video/webm",
    "m4v": "video/x-m4v", "3gp": "video/3gpp", "avi": "video/x-msvideo", "mkv": "video/x-matroska",
}


def _extension(filename: str) -> str:
    return (filename.rsplit(".", 1)[-1].lower() if filename and "." in filename else "")


def _nombre_unico_onedrive(filename: str, asignacion_id=None) -> str:
    """Prefija el nombre con asignación + id corto. OneDrive usa conflictBehavior=replace,
    así que dos videos con el mismo nombre (ej. 'video.mp4' de galería) se pisaban entre sí
    y ambas filas de la DB acababan apuntando al mismo archivo."""
    base = re.sub(r"[^\w.\- ]", "_", filename or "video.mp4")
    return f"A{asignacion_id or 0}_{uuid.uuid4().hex[:8]}_{base}"


def _tipo_de_archivo(filename: str) -> str:
    return "video" if _extension(filename) in VIDEO_EXTENSIONS else "foto"


# ── UTILIDAD: comprimir imagen ────────────────────────────────────────────
def comprimir_imagen(contenido: bytes, filename: str) -> bytes:
    """
    Redimensiona a MAX_DIMENSION px en el lado más largo y
    recodifica como JPEG a JPEG_QUALITY. Devuelve los bytes comprimidos.
    Si falla (ej. el archivo no es imagen) devuelve el original.
    """
    try:
        img = Image.open(io.BytesIO(contenido))

        # Preservar orientación EXIF
        try:
            from PIL import ImageOps
            img = ImageOps.exif_transpose(img)
        except Exception:
            pass

        # Redimensionar solo si es más grande que MAX_DIMENSION
        w, h = img.size
        if max(w, h) > MAX_DIMENSION:
            ratio = MAX_DIMENSION / max(w, h)
            img = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

        # Convertir a RGB (necesario para guardar como JPEG)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        out = io.BytesIO()
        img.save(out, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        compressed = out.getvalue()

        reduccion = (1 - len(compressed) / len(contenido)) * 100
        logger.info(f"[compress] {filename}: {len(contenido)//1024}KB → {len(compressed)//1024}KB ({reduccion:.0f}% menos)")
        return compressed
    except Exception as e:
        logger.warning(f"[compress] No se pudo comprimir {filename}: {e} — usando original")
        return contenido


# ── TAREA PARA UN SOLO ARCHIVO (foto o video) ─────────────────────────────
async def procesar_foto(file: UploadFile, unidad: str, tecnico: str, asignacion_id: int = None, equipo: str = None) -> dict:
    """Lee, comprime (si es foto) y guarda una foto o video. Devuelve
    {'filename', 'ok', 'error'}.

    Para VIDEO: si OneDrive está configurado, se sube ahí de forma SÍNCRONA
    (antes de responder) y en la DB solo se guarda la referencia
    (onedrive_item_id / onedrive_url) con contenido=NULL, para no llenar la
    base de datos de blobs pesados. Si OneDrive falla o no está configurado,
    se guarda el blob completo en la DB como respaldo (no se pierde la
    evidencia), igual que las fotos."""
    try:
        contenido = await file.read()
        tipo = _tipo_de_archivo(file.filename)

        if tipo == "video":
            if len(contenido) > MAX_VIDEO_BYTES:
                mb = MAX_VIDEO_BYTES // (1024 * 1024)
                return {"filename": file.filename, "ok": False,
                        "error": f"El video pesa más de {mb}MB. Comprímelo o recorta la duración."}
        else:
            # Comprimir solo si pesa más del umbral
            if len(contenido) > MAX_BYTES_BEFORE:
                contenido = await run_in_threadpool(comprimir_imagen, contenido, file.filename)

        mime_type = MIME_MAP.get(_extension(file.filename), file.content_type or "application/octet-stream")

        onedrive_item_id = None
        onedrive_url = None
        contenido_a_guardar = contenido

        if tipo == "video" and ONEDRIVE_ENABLED:
            try:
                resultado_od = await run_in_threadpool(
                    sync_video_evidencia, unidad, _nombre_unico_onedrive(file.filename, asignacion_id), contenido
                )
                onedrive_item_id = resultado_od.get("item_id") or None
                onedrive_url = resultado_od.get("webUrl") or None
                if onedrive_item_id:
                    # Subida a OneDrive exitosa: no duplicar el video pesado en la DB
                    contenido_a_guardar = None
            except Exception as e:
                logger.error(f"[OneDrive] Falló subida de video {file.filename}, se guarda en DB como respaldo: {e}")

        # La DB rechaza filas > 6 MB (error 8025): los archivos grandes van en trozos.
        if contenido_a_guardar is not None and len(contenido_a_guardar) > ep.DB_FILA_MAX:
            return await _guardar_grande_en_partes(
                file.filename, contenido_a_guardar, unidad, tecnico, asignacion_id, tipo, mime_type, equipo
            )

        # execute_write es una llamada SÍNCRONA a MySQL; si se llama directo
        # dentro de un endpoint async bloquea TODO el event loop (la app corre
        # con 1 solo worker en Clever Cloud). Con varias fotos subiendo a la
        # vez esto acumula bloqueo suficiente para que el gateway corte la
        # conexión antes de recibir respuesta. Se ejecuta en threadpool para
        # no bloquear el loop mientras se escribe el BLOB en la base de datos.
        try:
            ok = await run_in_threadpool(
                execute_write,
                "INSERT INTO evidencias (unit_number, nombre_archivo, contenido, tecnico, asignacion_id, tipo, mime_type, onedrive_item_id, onedrive_url, equipo) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (unidad, file.filename, contenido_a_guardar, tecnico, asignacion_id, tipo, mime_type, onedrive_item_id, onedrive_url, equipo)
            )
        except Exception as e_insert:
            # Columnas nuevas (tipo/mime_type/onedrive_*/equipo) aún no migradas
            # en la DB (deploy muy reciente) — no perder el archivo del técnico:
            # reintentar con el INSERT clásico. Si es un video y ya se subió a
            # OneDrive, se guarda igual el blob completo como respaldo porque
            # sin la columna onedrive_item_id no hay forma de solo guardar la
            # referencia.
            logger.warning(f"[evidencias] Fallback de INSERT sin columnas nuevas: {e_insert}")
            ok = await run_in_threadpool(
                execute_write,
                "INSERT INTO evidencias (unit_number, nombre_archivo, contenido, tecnico, asignacion_id) "
                "VALUES (%s,%s,%s,%s,%s)",
                (unidad, file.filename, contenido, tecnico, asignacion_id)
            )

        # OneDrive en background para FOTOS (el video ya se subió arriba, síncrono)
        if ok and tipo == "foto" and ONEDRIVE_ENABLED:
            asyncio.create_task(_sync_onedrive_bg(unidad, file.filename, contenido))

        if not ok:
            return {"filename": file.filename, "ok": False, "error": "No se pudo guardar en la base de datos"}
        return {"filename": file.filename, "ok": True, "error": None}
    except Exception as e:
        logger.error(f"[upload] Error procesando {file.filename}: {e}")
        return {"filename": file.filename, "ok": False, "error": str(e)}


def _insertar_fila_sin_contenido(filename, unidad, tecnico, asignacion_id, tipo, mime_type, equipo) -> int:
    """Crea la fila de `evidencias` con contenido NULL y devuelve su id."""
    try:
        eid = execute_write_with_id(
            "INSERT INTO evidencias (unit_number, nombre_archivo, contenido, tecnico, asignacion_id, tipo, mime_type, equipo) "
            "VALUES (%s,%s,NULL,%s,%s,%s,%s,%s)",
            (unidad, filename, tecnico, asignacion_id, tipo, mime_type, equipo),
        )
    except Exception as e:
        logger.warning(f"[evidencias] INSERT sin columnas nuevas (partes): {e}")
        eid = execute_write_with_id(
            "INSERT INTO evidencias (unit_number, nombre_archivo, contenido, tecnico, asignacion_id) VALUES (%s,%s,NULL,%s,%s)",
            (unidad, filename, tecnico, asignacion_id),
        )
    if not eid:   # por si el driver no devuelve el id: buscar la fila recién creada
        r = execute_read(
            "SELECT id FROM evidencias WHERE unit_number=%s AND nombre_archivo=%s AND tecnico=%s "
            "AND contenido IS NULL ORDER BY id DESC LIMIT 1", (unidad, filename, tecnico))
        eid = r[0]["id"] if r else None
    if not eid:
        raise Exception("No se pudo obtener el id de la evidencia")
    return eid


async def _guardar_grande_en_partes(filename, contenido, unidad, tecnico, asignacion_id, tipo, mime_type, equipo) -> dict:
    eid = None
    try:
        eid = await run_in_threadpool(_insertar_fila_sin_contenido, filename, unidad, tecnico, asignacion_id, tipo, mime_type, equipo)
        await run_in_threadpool(ep.guardar_partes, eid, contenido)
        logger.info(f"[evidencias] {filename} ({len(contenido)//1024}KB) guardado en partes, id={eid}")
        return {"filename": filename, "ok": True, "error": None}
    except Exception as e:
        logger.error(f"[evidencias] No se pudo guardar en partes {filename}: {e}")
        if eid:   # no dejar una fila sin archivo
            try:
                await run_in_threadpool(ep.borrar_partes, [eid])
                await run_in_threadpool(execute_write, "DELETE FROM evidencias WHERE id=%s", (eid,))
            except Exception:
                pass
        return {"filename": filename, "ok": False, "error": str(e)}


async def _sync_onedrive_bg(unidad: str, filename: str, contenido: bytes):
    """Sincroniza con OneDrive sin bloquear la respuesta principal."""
    try:
        await run_in_threadpool(sync_evidencia, unidad, filename, contenido)
    except Exception as e:
        logger.warning(f"[OneDrive] No se pudo subir {filename}: {e}")


# ── CONTAR FOTOS DE UNA UNIDAD/TÉCNICO ───────────────────────────────────
@router.get("/count")
def contar_evidencias(unit_number: str, tecnico: str, current_user=Depends(verify_token)):
    res = execute_read(
        "SELECT COUNT(*) AS total FROM evidencias WHERE unit_number=%s AND tecnico=%s",
        (unit_number, tecnico)
    )
    return {"total": res[0]["total"] if res else 0}


# ── TOTAL DE FOTOS POR UNIDAD ─────────────────────────────────────────────
@router.get("/total/{unit_number}")
def total_por_unidad(unit_number: str, current_user=Depends(verify_token)):
    res = execute_read(
        "SELECT COUNT(*) AS total FROM evidencias WHERE unit_number=%s", (unit_number,)
    )
    return {"total": res[0]["total"] if res else 0}


# ── CONTAR FOTOS DE UNA ACTIVIDAD ESPECÍFICA (asignación) ────────────────
@router.get("/count-asignacion/{asignacion_id}")
def contar_evidencias_asignacion(asignacion_id: int, current_user=Depends(verify_token)):
    res = execute_read(
        "SELECT COUNT(*) AS total, "
        "SUM(CASE WHEN COALESCE(tipo,'foto')='video' THEN 1 ELSE 0 END) AS videos "
        "FROM evidencias WHERE asignacion_id=%s",
        (asignacion_id,)
    )
    total = int(res[0]["total"]) if res else 0
    videos = int(res[0].get("videos") or 0) if res else 0
    return {"total": total, "videos": videos, "fotos": total - videos}


# ── LISTAR FOTOS DE UNA ACTIVIDAD ESPECÍFICA — solo admin/visor ──────────
@router.get("/por-actividad/{asignacion_id}")
def evidencias_por_actividad(asignacion_id: int, current_user=Depends(require_admin_or_visor)):
    try:
        rows = execute_read(
            """SELECT id, nombre_archivo, tecnico, unit_number, tipo, equipo,
                      COALESCE(created_at, '') AS fecha
               FROM evidencias
               WHERE asignacion_id=%s
               ORDER BY id ASC""",
            (asignacion_id,)
        )
    except Exception as e:
        # Columnas 'tipo'/'equipo' aún no migradas en la DB (deploy reciente) —
        # no tronar, responder igual sin esos campos.
        logger.warning(f"[evidencias] Fallback sin columna 'tipo'/'equipo' en por-actividad: {e}")
        rows = execute_read(
            """SELECT id, nombre_archivo, tecnico, unit_number,
                      COALESCE(created_at, '') AS fecha
               FROM evidencias
               WHERE asignacion_id=%s
               ORDER BY id ASC""",
            (asignacion_id,)
        )
    fotos = [{
        "id": r["id"],
        "nombre": r["nombre_archivo"] or f"foto_{r['id']}.jpg",
        "tecnico": r["tecnico"] or "",
        "equipo": r.get("equipo") or "",
        "unit_number": r["unit_number"],
        "tipo": r.get("tipo") or "foto",
        "fecha": str(r["fecha"]) if r["fecha"] else "",
    } for r in (rows or [])]
    return {"asignacion_id": asignacion_id, "total": len(fotos), "fotos": fotos}


# ── LISTAR EVIDENCIA PROPIA DE UNA ACTIVIDAD — técnico dueño, o admin/visor ──
# A diferencia de /por-actividad (solo admin/visor), esta ruta la puede usar
# el propio técnico para revisar, antes de subir más, lo que ya subió para
# ESA actividad puntual — validando que la actividad sea suya (si no es
# admin/visor), para no exponer evidencia de actividades ajenas.
@router.get("/mis-evidencias/{asignacion_id}")
def mis_evidencias(asignacion_id: int, current_user=Depends(verify_token)):
    if current_user["role"] not in ("admin", "visor", "lider"):
        propia = execute_read(
            "SELECT 1 FROM asignaciones WHERE id=%s AND tecnico=%s",
            (asignacion_id, current_user["username"])
        )
        if not propia:
            raise HTTPException(status_code=403, detail="Esta actividad no te pertenece")
    try:
        rows = execute_read(
            """SELECT id, nombre_archivo, tecnico, tipo,
                      COALESCE(created_at, '') AS fecha
               FROM evidencias WHERE asignacion_id=%s ORDER BY id ASC""",
            (asignacion_id,)
        )
    except Exception as e:
        logger.warning(f"[evidencias] Fallback sin columna 'tipo' en mis-evidencias: {e}")
        rows = execute_read(
            """SELECT id, nombre_archivo, tecnico,
                      COALESCE(created_at, '') AS fecha
               FROM evidencias WHERE asignacion_id=%s ORDER BY id ASC""",
            (asignacion_id,)
        )
    evidencias = [{
        "id": r["id"],
        "nombre": r["nombre_archivo"] or f"evidencia_{r['id']}",
        "tecnico": r.get("tecnico") or "",
        "tipo": r.get("tipo") or "foto",
        "fecha": str(r["fecha"]) if r.get("fecha") else "",
    } for r in (rows or [])]
    return {"asignacion_id": asignacion_id, "total": len(evidencias), "evidencias": evidencias}


# ── SUBIR FOTOS ───────────────────────────────────────────────────────────
@router.post("/upload")
async def subir_evidencias(
    unidad: str = Form(...),
    tecnico: str = Form(...),
    files: List[UploadFile] = File(...),
    asignacion_id: int = Form(None),
    equipo: str = Form(None),
    current_user=Depends(verify_token)
):
    # Verificar límite
    # El tope de MAX_FOTOS se aplica por actividad (asignacion_id) cuando se
    # conoce, para que cada finalización de actividad permita hasta 100 fotos
    # sin importar cuántas se hayan subido ya en otras actividades de la misma
    # unidad. Si no viene asignacion_id (uso legado), se conserva el límite
    # acumulado por unidad+técnico como respaldo.
    if asignacion_id is not None:
        res = await run_in_threadpool(
            execute_read,
            "SELECT COUNT(*) AS total FROM evidencias WHERE asignacion_id=%s",
            (asignacion_id,)
        )
        limite_detalle = "para esta actividad"
    else:
        res = await run_in_threadpool(
            execute_read,
            "SELECT COUNT(*) AS total FROM evidencias WHERE unit_number=%s AND tecnico=%s",
            (unidad, tecnico)
        )
        limite_detalle = "para esta unidad"

    ya_guardadas = res[0]["total"] if res else 0
    disponibles  = MAX_FOTOS - ya_guardadas
    if disponibles <= 0:
        raise HTTPException(
            status_code=400,
            detail=f"Ya alcanzaste el límite de {MAX_FOTOS} fotos {limite_detalle}"
        )

    files_a_guardar = files[:disponibles]
    if tecnico != current_user["username"]:       # auditoría: quién subió a nombre de quién
        logger.info(f"[evidencias] '{current_user['username']}' ({current_user.get('role')}) sube "
                    f"{len(files_a_guardar)} archivo(s) a nombre de '{tecnico}' (unidad {unidad}, tarea {asignacion_id})")

    # ── Normalizar equipo: lista de usernames separados por coma, sin        ─
    # duplicados, quien sube siempre incluido (aunque no lo haya marcado). ──
    equipo_normalizado = None
    if equipo:
        nombres = [n.strip() for n in equipo.split(",") if n.strip()]
        vistos, ordenados = set(), []
        for n in [tecnico] + nombres:
            if n not in vistos:
                vistos.add(n)
                ordenados.append(n)
        if len(ordenados) > 1:
            equipo_normalizado = ", ".join(ordenados)

    # ── Procesar en paralelo con semáforo para no saturar DB/red ──────────
    semaforo = asyncio.Semaphore(MAX_CONCURRENT)
    semaforo_video = asyncio.Semaphore(MAX_CONCURRENT_VIDEO)

    async def procesar_con_limite(file):
        sem = semaforo_video if _tipo_de_archivo(file.filename) == "video" else semaforo
        async with sem:
            return await procesar_foto(file, unidad, tecnico, asignacion_id, equipo_normalizado)

    resultados = await asyncio.gather(
        *[procesar_con_limite(f) for f in files_a_guardar],
        return_exceptions=False
    )

    guardadas = sum(1 for r in resultados if r["ok"])
    fallidas  = [r["filename"] for r in resultados if not r["ok"]]

    if guardadas == 0 and resultados:
        errores = "; ".join(f"{r['filename']}: {r['error']}" for r in resultados if r["error"])
        # 400 = error permanente (ej. video muy pesado): el cliente NO reintenta.
        # 500 = fallo transitorio: el cliente reintenta y conserva su copia local.
        permanente = any("pesa más de" in (r["error"] or "") for r in resultados)
        raise HTTPException(
            status_code=400 if permanente else 500,
            detail=errores or "No se pudo guardar la evidencia",
        )

    respuesta = {
        "mensaje"  : f"{guardadas} archivo(s) guardado(s)",
        "guardadas": guardadas,
        "total_enviadas": len(files_a_guardar),
    }
    if fallidas:
        respuesta["fallidas"] = fallidas
        respuesta["errores"] = {r["filename"]: r["error"] for r in resultados if not r["ok"]}
    if ONEDRIVE_ENABLED:
        respuesta["onedrive"] = "sincronización en segundo plano"

    return respuesta


# ── DESCARGAR ZIP DE TODAS LAS FOTOS DE UNA UNIDAD ───────────────────────
@router.get("/download/{unit_number}")
async def descargar_evidencias(unit_number: str, current_user=Depends(require_admin_or_visor)):
    meta = execute_read(
        "SELECT id, nombre_archivo, contenido IS NULL AS sin_blob, onedrive_item_id FROM evidencias WHERE unit_number=%s",
        (unit_number,)
    )
    if not meta:
        raise HTTPException(status_code=404, detail="No hay evidencias para esta unidad")

    # Traer los contenidos que SÍ están en la DB en una sola query (evita N queries)
    ids_con_blob = tuple(m["id"] for m in meta if not m["sin_blob"])
    contenidos = {}
    if ids_con_blob:
        placeholders = ",".join(["%s"] * len(ids_con_blob))
        filas = execute_read(
            f"SELECT id, contenido FROM evidencias WHERE id IN ({placeholders})", ids_con_blob
        )
        contenidos = {f["id"]: f["contenido"] for f in filas if f["contenido"]}

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
        nombres_vistos = {}
        for m in meta:
            contenido = contenidos.get(m["id"])
            if contenido is None and m.get("onedrive_item_id"):
                # Video que solo vive en OneDrive: se descarga aquí para incluirlo en el ZIP
                try:
                    contenido = await run_in_threadpool(download_item_bytes, m["onedrive_item_id"])
                except Exception as e:
                    logger.error(f"[OneDrive] No se pudo incluir en el ZIP la evidencia {m['id']}: {e}")
                    continue
            if contenido is None:
                contenido = await run_in_threadpool(ep.leer_partes, m["id"])   # archivo grande guardado en partes
            if not contenido:
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
            zf.writestr(nombre, contenido)

    buf.seek(0)
    zip_bytes = buf.getvalue()

    if ONEDRIVE_ENABLED:
        asyncio.ensure_future(
            run_in_threadpool(sync_zip_evidencias, unit_number, zip_bytes)
        )

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
def sync_unidad_onedrive(unit_number: str, current_user=Depends(verify_token)):
    if not ONEDRIVE_ENABLED:
        raise HTTPException(status_code=503, detail="OneDrive no está configurado")

    meta = execute_read(
        "SELECT id, nombre_archivo FROM evidencias WHERE unit_number=%s",
        (unit_number,)
    )
    if not meta:
        raise HTTPException(status_code=404, detail="No hay evidencias para esta unidad")

    ids = tuple(m["id"] for m in meta)
    placeholders = ",".join(["%s"] * len(ids))
    filas = execute_read(
        f"SELECT id, contenido FROM evidencias WHERE id IN ({placeholders})", ids
    )
    contenidos = {f["id"]: f["contenido"] for f in filas if f["contenido"]}

    subidas = 0
    errores = 0
    for m in meta:
        contenido = contenidos.get(m["id"])
        if not contenido:
            continue
        try:
            sync_evidencia(unit_number, m["nombre_archivo"] or f"foto_{m['id']}.jpg", contenido)
            subidas += 1
        except Exception as e:
            logger.error(f"[OneDrive] Error en foto id={m['id']}: {e}")
            errores += 1

    return {
        "mensaje": f"Sincronización completada para {unit_number}",
        "subidas": subidas,
        "errores": errores,
    }


# ── LISTAR FOTOS DE UNA UNIDAD (sin binarios) — solo admin/visor ──────────
@router.get("/lista/{unit_number}")
def listar_evidencias(
    unit_number: str,
    page: int = 1,
    per_page: int = 20,
    tipo: Optional[str] = None,            # 'video' | 'foto' (vacío = todo)
    asignacion_id: Optional[int] = None,   # solo los archivos de una actividad
    current_user=Depends(require_admin_or_visor)
):
    offset = (page - 1) * per_page
    where, params = ["e.unit_number=%s"], [unit_number]
    if tipo in ("video", "foto"):
        where.append("COALESCE(e.tipo,'foto')=%s")
        params.append(tipo)
    if asignacion_id is not None:
        where.append("e.asignacion_id=%s")
        params.append(asignacion_id)
    cond = " AND ".join(where)
    total_res = execute_read(f"SELECT COUNT(*) AS total FROM evidencias e WHERE {cond}", tuple(params))
    total = total_res[0]["total"] if total_res else 0

    try:
        # Orden por FECHA (no por id): en esta base los id no crecen en orden cronológico.
        rows = execute_read(
            f"""SELECT e.id, e.nombre_archivo, e.tecnico, e.asignacion_id, e.tipo, e.equipo,
                      COALESCE(e.created_at, '') AS fecha,
                      a.actividad_id AS actividad
               FROM evidencias e
               LEFT JOIN asignaciones a ON a.id = e.asignacion_id
               WHERE {cond}
               ORDER BY e.created_at DESC, e.id DESC
               LIMIT %s OFFSET %s""",
            tuple(params) + (per_page, offset)
        )
    except Exception as e:
        # Columnas 'tipo'/'equipo' aún no migradas en la DB (deploy reciente) —
        # no tronar, responder igual sin esos campos.
        logger.warning(f"[evidencias] Fallback sin columna 'tipo'/'equipo' en lista: {e}")
        rows = execute_read(
            """SELECT e.id, e.nombre_archivo, e.tecnico, e.asignacion_id,
                      COALESCE(e.created_at, '') AS fecha,
                      a.actividad_id AS actividad
               FROM evidencias e
               LEFT JOIN asignaciones a ON a.id = e.asignacion_id
               WHERE e.unit_number=%s
               ORDER BY e.id DESC
               LIMIT %s OFFSET %s""",
            (unit_number, per_page, offset)
        )
    fotos = []
    for r in (rows or []):
        fotos.append({
            "id": r["id"],
            "nombre": r["nombre_archivo"] or f"foto_{r['id']}.jpg",
            "tecnico": r["tecnico"] or "",
            "equipo": r.get("equipo") or "",
            "tipo": r.get("tipo") or "foto",
            "fecha": str(r["fecha"]) if r["fecha"] else "",
            "actividad": r.get("actividad") or "",
            "asignacion_id": r.get("asignacion_id"),
        })

    return {
        "unit_number": unit_number,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max(1, -(-total // per_page)),
        "fotos": fotos,
    }


# ── LISTAR TODAS LAS UNIDADES CON EVIDENCIAS — solo admin/visor ───────────
@router.get("/unidades-con-fotos")
def unidades_con_fotos(current_user=Depends(require_admin_or_visor)):
    # Mismo criterio que el dashboard: solo unidades de lotes activos (oculto=0),
    # ordenadas por lote y luego por número de unidad para que la vista de
    # evidencias no aparezca mezclada.
    rows = execute_read(
        """SELECT e.unit_number AS unit_number, COUNT(*) AS total, u.id_lote AS id_lote,
                  SUM(CASE WHEN e.tipo='video' THEN 1 ELSE 0 END) AS videos
           FROM evidencias e
           INNER JOIN unidades u ON u.unit_number = e.unit_number
           WHERE u.oculto = 0
           GROUP BY e.unit_number, u.id_lote
           ORDER BY u.id_lote, e.unit_number"""
    )
    return [{"unit_number": r["unit_number"], "total": r["total"], "id_lote": r["id_lote"],
             "videos": int(r.get("videos") or 0)} for r in (rows or [])]


# ── SERVIR UNA FOTO O VIDEO INDIVIDUAL — solo admin/visor ─────────────────
@router.get("/foto/{foto_id}")
def ver_foto(foto_id: int, range: Optional[str] = Header(None), current_user=Depends(require_admin_or_visor)):
    try:
        rows = execute_read(
            "SELECT nombre_archivo, contenido, mime_type, tipo, onedrive_item_id FROM evidencias WHERE id=%s",
            (foto_id,)
        )
    except Exception as e:
        logger.warning(f"[evidencias] Fallback sin columnas nuevas en ver_foto: {e}")
        rows = execute_read(
            "SELECT nombre_archivo, contenido FROM evidencias WHERE id=%s",
            (foto_id,)
        )
        if rows:
            rows[0]["mime_type"] = None
            rows[0]["tipo"] = "foto"
            rows[0]["onedrive_item_id"] = None
    if not rows:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    row = rows[0]
    nombre = row["nombre_archivo"] or "foto.jpg"
    ext = _extension(nombre)
    media_type = row.get("mime_type") or MIME_MAP.get(ext, "application/octet-stream")
    es_video = (row.get("tipo") == "video")

    # ── Archivo que vive solo en OneDrive (no se guardó el blob en la DB) ───
    # Antes se hacía RedirectResponse a la URL de descarga de Microsoft. El visor
    # usa fetch() con Authorization, y esa URL no devuelve cabeceras CORS, así que
    # el navegador bloqueaba el video y aparecía "Error al cargar este video"
    # aunque el archivo SÍ existía en OneDrive. Ahora el backend lo transmite
    # (streaming + Range) para que funcione en fetch(), <video> y móviles.
    if not row["contenido"] and row.get("onedrive_item_id"):
        try:
            download_url = get_download_url(row["onedrive_item_id"])
            if not download_url:
                raise Exception("OneDrive no devolvió URL de descarga")
            req_headers = {"Range": range} if range else {}
            upstream = requests.get(download_url, headers=req_headers, stream=True, timeout=(10, 60))
            if upstream.status_code not in (200, 206):
                upstream.close()
                raise Exception(f"OneDrive respondió {upstream.status_code}")
            headers = {"Accept-Ranges": "bytes", "Cache-Control": "private, max-age=3600"}
            for h in ("Content-Length", "Content-Range"):
                if upstream.headers.get(h):
                    headers[h] = upstream.headers[h]
            return StreamingResponse(
                upstream.iter_content(chunk_size=256 * 1024),
                status_code=upstream.status_code,
                media_type=media_type,
                headers=headers,
                background=BackgroundTask(upstream.close),
            )
        except Exception as e:
            logger.error(f"[OneDrive] No se pudo obtener el archivo de evidencia {foto_id}: {e}")
            raise HTTPException(status_code=502, detail="No se pudo obtener el archivo desde OneDrive")

    if not row["contenido"]:
        total_partes = ep.tamano_total(foto_id)
        if not total_partes:
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        # Archivo grande guardado en trozos (ver evidencia_partes.py), con soporte de Range
        inicio, fin, codigo = 0, total_partes - 1, 200
        if range:
            try:
                ini_s, fin_s = range.split("=")[1].split("-")
                inicio = int(ini_s) if ini_s else 0
                fin = min(int(fin_s) if fin_s else total_partes - 1, total_partes - 1)
                codigo = 206
            except Exception:
                inicio, fin, codigo = 0, total_partes - 1, 200
        hdrs = {"Accept-Ranges": "bytes", "Content-Length": str(fin - inicio + 1), "Cache-Control": "private, max-age=3600"}
        if codigo == 206:
            hdrs["Content-Range"] = f"bytes {inicio}-{fin}/{total_partes}"
        return StreamingResponse(ep.iterar_rango(foto_id, inicio, fin), status_code=codigo, media_type=media_type, headers=hdrs)

    contenido = row["contenido"]
    contenido = bytes(contenido) if not isinstance(contenido, bytes) else contenido

    if not es_video:
        return Response(
            content=contenido,
            media_type=media_type,
            headers={"Cache-Control": "private, max-age=3600"},
        )

    # ── Video con blob local (respaldo cuando OneDrive no está disponible):
    # soporta Range requests para que el navegador pueda hacer streaming/seek
    total = len(contenido)
    if range is None:
        return Response(
            content=contenido,
            media_type=media_type,
            headers={"Cache-Control": "private, max-age=3600", "Accept-Ranges": "bytes"},
        )

    try:
        _, rango = range.split("=")
        start_s, end_s = rango.split("-")
        start = int(start_s) if start_s else 0
        end = int(end_s) if end_s else total - 1
        end = min(end, total - 1)
    except Exception:
        start, end = 0, total - 1

    chunk = contenido[start:end + 1]
    headers = {
        "Content-Range": f"bytes {start}-{end}/{total}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(len(chunk)),
        "Cache-Control": "private, max-age=3600",
    }
    return Response(content=chunk, media_type=media_type, headers=headers, status_code=206)


# ── VER UNA EVIDENCIA PROPIA — técnico dueño de la actividad, o admin/visor ──
# Reutiliza toda la lógica de servir el archivo de ver_foto() (incluye el
# soporte de Range para reproducir/buscar en video); solo agrega una
# validación de que la evidencia pertenezca a una actividad del técnico
# que la pide, cuando no es admin/visor/líder.
@router.get("/mi-foto/{foto_id}")
def mi_foto(foto_id: int, range: Optional[str] = Header(None), current_user=Depends(verify_token)):
    if current_user["role"] not in ("admin", "visor", "lider"):
        propia = execute_read(
            """SELECT 1 FROM evidencias e INNER JOIN asignaciones a ON a.id = e.asignacion_id
               WHERE e.id=%s AND a.tecnico=%s""",
            (foto_id, current_user["username"])
        )
        if not propia:
            raise HTTPException(status_code=403, detail="Esta evidencia no te pertenece")
    return ver_foto(foto_id, range)


# ── ELIMINAR FOTOS SELECCIONADAS — solo admin ─────────────────────────────
@router.post("/eliminar")
def eliminar_evidencias(data: dict, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden eliminar evidencias")

    ids = data.get("ids") or []
    ids = [int(i) for i in ids if str(i).isdigit()]
    if not ids:
        raise HTTPException(status_code=400, detail="No se proporcionaron IDs válidos")

    placeholders = ",".join(["%s"] * len(ids))
    try:
        ep.borrar_partes(ids)
    except Exception as e:
        logger.warning(f"[evidencias] no se pudieron borrar partes: {e}")
    execute_write(
        f"DELETE FROM evidencias WHERE id IN ({placeholders})", tuple(ids)
    )
    return {"mensaje": f"{len(ids)} foto(s) eliminada(s)", "ids": ids}


# ── DIAGNÓSTICO: ¿dónde quedaron los videos? — solo admin ─────────────────
@router.get("/diagnostico")
def diagnostico_evidencias(current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    rows = execute_read(
        """SELECT e.id, e.unit_number, e.nombre_archivo, e.tecnico, e.asignacion_id,
                  e.onedrive_item_id, e.onedrive_url,
                  (e.contenido IS NOT NULL) AS en_db,
                  (SELECT COUNT(*) FROM evidencia_partes p WHERE p.evidencia_id = e.id) AS n_partes,
                  COALESCE(e.created_at, '') AS fecha,
                  a.estado AS estado_actividad, a.actividad_id AS actividad
           FROM evidencias e
           LEFT JOIN asignaciones a ON a.id = e.asignacion_id
           WHERE e.tipo='video'
           ORDER BY e.id DESC LIMIT 500"""
    )
    def _dest(r):
        if r["en_db"]: return "base_de_datos"
        if r.get("n_partes"): return "base_de_datos(partes)"
        if r["onedrive_item_id"]: return "onedrive"
        return "PERDIDO"          # fila sin archivo en ningún lado
    videos = [{**{k: (str(v) if k == "fecha" else v) for k, v in r.items() if k not in ("en_db", "n_partes")},
               "ubicacion": _dest(r), "sin_actividad": r["asignacion_id"] is None} for r in (rows or [])]
    resumen = {}
    for v in videos:
        resumen[v["ubicacion"]] = resumen.get(v["ubicacion"], 0) + 1
    # actividades completadas sin ninguna evidencia (foto o video)
    sin_evid = execute_read(
        """SELECT a.id, a.unidad, a.actividad_id, a.tecnico, a.fecha_fin
           FROM asignaciones a
           LEFT JOIN evidencias e ON e.asignacion_id = a.id
           WHERE a.estado='completada' AND e.id IS NULL
           ORDER BY a.id DESC LIMIT 200"""
    )
    return {
        "resumen_videos": resumen,
        "videos": videos,
        "actividades_completadas_sin_evidencia": [
            {**r, "fecha_fin": str(r["fecha_fin"]) if r.get("fecha_fin") else ""} for r in (sin_evid or [])
        ],
    }


# ── REPARAR VIDEOS "ATORADOS" — solo admin ────────────────────────────────
# Casos que hacen que un video exista pero no se vea en la app:
#  A) La fila quedó con tipo='foto' (el INSERT de respaldo no guardaba 'tipo'),
#     así que la app intenta pintarla como imagen y falla.
#  B) La fila no tiene archivo (contenido NULL y sin onedrive_item_id) pero el
#     video SÍ está en OneDrive -> se vuelve a enlazar por unidad + nombre.
#  C) El video está en OneDrive pero no hay NINGUNA fila en la DB -> se registra.
# Con aplicar=false (por defecto) NO modifica nada: solo informa lo que haría.
_VIDEO_REGEX = "[.](mp4|mov|webm|m4v|3gp|avi|mkv)$"


@router.post("/reparar")
def reparar_videos(aplicar: bool = False, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    informe = {"modo": "APLICADO" if aplicar else "SIMULACIÓN (no se cambió nada)"}

    # A) videos clasificados como foto / sin mime
    mal = execute_read(
        "SELECT id, nombre_archivo FROM evidencias "
        "WHERE (tipo IS NULL OR tipo<>'video') AND LOWER(nombre_archivo) REGEXP %s", (_VIDEO_REGEX,)
    ) or []
    sin_mime = execute_read(
        "SELECT id, nombre_archivo FROM evidencias WHERE tipo='video' AND (mime_type IS NULL OR mime_type='')"
    ) or []
    if aplicar:
        for r in list(mal) + list(sin_mime):
            execute_write(
                "UPDATE evidencias SET tipo='video', mime_type=%s WHERE id=%s",
                (MIME_MAP.get(_extension(r["nombre_archivo"]), "video/mp4"), r["id"]),
            )
    informe["A_reclasificados_como_video"] = len(mal) + len(sin_mime)
    informe["A_ejemplos"] = [r["nombre_archivo"] for r in (list(mal) + list(sin_mime))[:20]]

    # Videos que la app no muestra por la unidad (lote oculto o unidad inexistente)
    invisibles = execute_read(
        "SELECT e.id, e.unit_number, e.nombre_archivo FROM evidencias e "
        "LEFT JOIN unidades u ON u.unit_number = e.unit_number "
        "WHERE LOWER(e.nombre_archivo) REGEXP %s AND (u.unit_number IS NULL OR u.oculto=1) LIMIT 50",
        (_VIDEO_REGEX,),
    ) or []
    informe["videos_en_unidad_oculta_o_inexistente"] = [
        {"id": r["id"], "unidad": r["unit_number"], "archivo": r["nombre_archivo"]} for r in invisibles
    ]

    if not ONEDRIVE_ENABLED:
        informe["onedrive"] = "no configurado: no se pudieron revisar los casos B y C"
        return informe

    from onedrive_service import listar_videos_evidencias, re_split_unit_number
    try:
        archivos = listar_videos_evidencias()
    except Exception as e:
        informe["onedrive_error"] = str(e)[:300]
        return informe
    informe["videos_encontrados_en_onedrive"] = len(archivos)

    usados = {r["onedrive_item_id"] for r in (execute_read(
        "SELECT onedrive_item_id FROM evidencias WHERE onedrive_item_id IS NOT NULL AND onedrive_item_id<>''") or [])}
    unidades = {r["unit_number"] for r in (execute_read("SELECT unit_number FROM unidades") or [])}

    def _unidad_de(f):
        c = f["carpeta"]
        for cand in (re_split_unit_number(c), c):
            if cand in unidades:
                return cand
        return None

    # B) filas sin archivo -> enlazar con el video de OneDrive
    vacias = execute_read(
        "SELECT id, unit_number, nombre_archivo FROM evidencias "
        "WHERE contenido IS NULL AND (onedrive_item_id IS NULL OR onedrive_item_id='') "
        "AND NOT EXISTS (SELECT 1 FROM evidencia_partes p WHERE p.evidencia_id = evidencias.id) "
        "AND LOWER(nombre_archivo) REGEXP %s", (_VIDEO_REGEX,)
    ) or []
    reenlazadas, sin_archivo = [], []
    for r in vacias:
        nombre = r["nombre_archivo"] or ""
        cand = next((f for f in archivos
                     if f["id"] not in usados and _unidad_de(f) == r["unit_number"]
                     and (f["name"] == nombre or f["name"].endswith("_" + nombre))), None)
        if cand:
            usados.add(cand["id"])
            reenlazadas.append(r["id"])
            if aplicar:
                execute_write(
                    "UPDATE evidencias SET onedrive_item_id=%s, onedrive_url=%s, tipo='video', "
                    "mime_type=COALESCE(NULLIF(mime_type,''), %s) WHERE id=%s",
                    (cand["id"], cand["webUrl"], MIME_MAP.get(_extension(cand["name"]), "video/mp4"), r["id"]),
                )
        else:
            sin_archivo.append({"id": r["id"], "unidad": r["unit_number"], "archivo": nombre})
    informe["B_filas_reenlazadas_a_onedrive"] = len(reenlazadas)
    informe["B_filas_SIN_archivo_irrecuperables"] = sin_archivo[:50]

    # C) videos en OneDrive sin fila -> registrarlos
    huerfanos, ignorados = [], []
    for f in archivos:
        if f["id"] in usados:
            continue
        unidad = _unidad_de(f)
        if not unidad:
            ignorados.append(f["ruta"] + "/" + f["name"])
            continue
        m = re.match(r"^A(\d+)_[0-9a-f]{8}_", f["name"])
        asig_id = int(m.group(1)) if m and int(m.group(1)) > 0 else None
        tecnico = ""
        if asig_id:
            a = execute_read("SELECT tecnico FROM asignaciones WHERE id=%s", (asig_id,))
            if a: tecnico = a[0]["tecnico"] or ""
            else: asig_id = None
        huerfanos.append({"archivo": f["name"], "unidad": unidad, "asignacion_id": asig_id})
        if aplicar:
            fecha = (f["modificado"] or "").replace("T", " ").rstrip("Z") or None
            execute_write(
                "INSERT INTO evidencias (unit_number, nombre_archivo, contenido, tecnico, asignacion_id, "
                "tipo, mime_type, onedrive_item_id, onedrive_url, created_at) "
                "VALUES (%s,%s,NULL,%s,%s,'video',%s,%s,%s,COALESCE(%s, NOW()))",
                (unidad, f["name"], tecnico, asig_id, MIME_MAP.get(_extension(f["name"]), "video/mp4"),
                 f["id"], f["webUrl"], fecha),
            )
    informe["C_videos_en_onedrive_sin_fila_registrados"] = len(huerfanos)
    informe["C_ejemplos"] = huerfanos[:20]
    informe["C_ignorados_carpeta_no_reconocida"] = ignorados[:20]
    return informe


# ── COPIAR VIDEOS DE LA DB A ONEDRIVE — solo admin ────────────────────────
# Videos que hoy viven como blob en la base de datos (respaldo cuando OneDrive
# falló al subirlos). Se COPIAN a OneDrive y, SOLO si OneDrive confirma el mismo
# tamaño en bytes, se enlaza la fila (onedrive_item_id / onedrive_url).
# NO SE BORRA NADA DE LA DB: el blob (contenido) se conserva intacto, así que
# el video sigue disponible en la base aunque algo falle después. Liberar el
# espacio de la DB sería un paso aparte, que hoy no existe a propósito.
# Se procesa por tandas (limite) para no agotar la RAM de la instancia ni topar
# con el timeout del gateway; se llama varias veces hasta que pendientes = 0.
MIGRACION_PRESUPUESTO_SEG = 90   # corta la tanda antes del timeout del gateway


@router.post("/copiar-videos-a-onedrive")
def copiar_videos_a_onedrive(aplicar: bool = False, limite: int = 2, desde_id: int = 0,
                             current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    if not ONEDRIVE_ENABLED:
        raise HTTPException(status_code=503, detail="OneDrive no está configurado")
    limite = max(1, min(int(limite), 10))

    filtro = ("contenido IS NOT NULL AND (onedrive_item_id IS NULL OR onedrive_item_id='') "
              "AND (tipo='video' OR LOWER(nombre_archivo) REGEXP %s) AND id > %s")
    tot = execute_read(
        f"SELECT COUNT(*) AS n, COALESCE(SUM(LENGTH(contenido)),0) AS bytes FROM evidencias WHERE {filtro}",
        (_VIDEO_REGEX, desde_id),
    )
    pendientes = int(tot[0]["n"]) if tot else 0
    mb_pendientes = round(float(tot[0]["bytes"]) / 1048576, 1) if tot else 0.0
    informe = {
        "modo": "APLICADO" if aplicar else "SIMULACIÓN (no se cambió nada)",
        "pendientes_en_db": pendientes,
        "mb_pendientes_en_db": mb_pendientes,
    }

    # Sin cargar los blobs: solo metadatos y tamaño
    cand = execute_read(
        "SELECT id, unit_number, nombre_archivo, asignacion_id, mime_type, LENGTH(contenido) AS bytes "
        f"FROM evidencias WHERE {filtro} ORDER BY id LIMIT %s",
        (_VIDEO_REGEX, desde_id, limite),
    ) or []
    informe["tanda"] = [{"id": r["id"], "unidad": r["unit_number"], "archivo": r["nombre_archivo"],
                         "mb": round(float(r["bytes"]) / 1048576, 1)} for r in cand]
    if not aplicar:
        return informe

    from onedrive_service import tamano_item
    inicio = time.monotonic()
    migrados, errores = [], []
    ultimo_id = desde_id
    for r in cand:
        if time.monotonic() - inicio > MIGRACION_PRESUPUESTO_SEG:
            break                       # el resto va en la siguiente llamada
        ultimo_id = r["id"]
        contenido = None
        try:
            fila = execute_read("SELECT contenido FROM evidencias WHERE id=%s", (r["id"],))
            contenido = fila[0]["contenido"] if fila else None
            if not contenido:
                raise Exception("la fila ya no tiene contenido en la DB")
            contenido = bytes(contenido) if not isinstance(contenido, bytes) else contenido
            nombre = r["nombre_archivo"] or f"video_{r['id']}.mp4"
            res = sync_video_evidencia(r["unit_number"], _nombre_unico_onedrive(nombre, r["asignacion_id"]), contenido)
            item_id = res.get("item_id")
            if not item_id:
                raise Exception("OneDrive no devolvió el id del archivo")
            subido = tamano_item(item_id)
            if subido != len(contenido):
                raise Exception(f"tamaño distinto en OneDrive ({subido} vs {len(contenido)} bytes); se conserva en la DB")
            execute_write(
                "UPDATE evidencias SET onedrive_item_id=%s, onedrive_url=%s, tipo='video', "
                "mime_type=COALESCE(NULLIF(mime_type,''), %s) WHERE id=%s",
                (item_id, res.get("webUrl", ""), MIME_MAP.get(_extension(nombre), "video/mp4"), r["id"]),
            )
            migrados.append({"id": r["id"], "archivo": nombre})
        except Exception as e:
            logger.error(f"[copiar-videos] id={r['id']}: {e}")
            errores.append({"id": r["id"], "archivo": r["nombre_archivo"], "error": str(e)[:200]})
        finally:
            contenido = None            # liberar RAM antes del siguiente video

    informe["migrados"] = migrados
    informe["errores"] = errores
    informe["pendientes_restantes"] = max(0, pendientes - len(migrados))
    informe["siguiente_desde_id"] = ultimo_id
    return informe


# ── VERIFICAR VIDEOS POR UNIDAD Y TAREA — solo admin ──────────────────────
# Solo lectura. Para cada video dice dónde está (DB / OneDrive / PERDIDO) y si
# la app lo puede mostrar donde se subió (unidad + tarea), con la razón exacta
# cuando no. Usa las mismas reglas que el visor de evidencias:
#  - la lista de unidades con evidencias solo incluye unidades que EXISTEN y no
#    están ocultas (ver /unidades-con-fotos);
#  - dentro de una tarea solo salen las filas con asignacion_id de esa tarea;
#  - un tipo distinto de 'video' se intenta pintar como imagen.
def _evaluar_video(r: dict) -> dict:
    """Devuelve ubicación, problemas (impiden verlo), avisos y si es reparable."""
    if r.get("en_db") or r.get("n_partes"):      # blob único, o archivo grande guardado en trozos
        ubicacion = "base_de_datos"
    elif r.get("onedrive_item_id"):
        ubicacion = "onedrive"
    else:
        ubicacion = "PERDIDO"
    problemas, avisos = [], []
    if ubicacion == "PERDIDO":
        problemas.append("La fila no tiene archivo (ni en la base ni en OneDrive).")
    if (r.get("tipo") or "") != "video":
        problemas.append("Está guardado como foto: la app intenta mostrarlo como imagen.")
    if r.get("u_unit") is None:
        problemas.append("La unidad no existe en Registro de unidades: no sale en la lista de evidencias.")
    elif r.get("u_oculto"):
        problemas.append("La unidad está oculta (lote oculto): no sale en la lista de evidencias.")
    if r.get("asignacion_id") is None:
        problemas.append("No está ligado a ninguna tarea: no aparece dentro de una tarea.")
    elif r.get("a_id") is None:
        problemas.append("La tarea a la que pertenece ya no existe.")
    elif r.get("a_unidad") and r["a_unidad"] != r.get("unit_number"):
        avisos.append(f"La tarea es de la unidad {r['a_unidad']}, pero el video está en {r.get('unit_number')}.")
    return {
        "ubicacion": ubicacion,
        "visible": not problemas,
        "problemas": problemas,
        "avisos": avisos,
        # 'Reparar' arregla: tipo incorrecto y filas sin archivo que sí están en OneDrive
        "reparable": (r.get("tipo") or "") != "video" or ubicacion == "PERDIDO",
    }


@router.get("/verificar-videos")
def verificar_videos(solo_problemas: bool = False, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    rows = execute_read(
        """SELECT e.id, e.unit_number, e.nombre_archivo, e.tecnico, e.asignacion_id, e.tipo,
                  e.onedrive_item_id, (e.contenido IS NOT NULL) AS en_db,
                  (SELECT COUNT(*) FROM evidencia_partes p WHERE p.evidencia_id = e.id) AS n_partes,
                  LENGTH(e.contenido) AS bytes_db, COALESCE(e.created_at, '') AS fecha,
                  u.unit_number AS u_unit, u.oculto AS u_oculto, u.id_lote AS id_lote,
                  a.id AS a_id, a.unidad AS a_unidad, a.actividad_id AS actividad, a.estado AS estado_tarea
           FROM evidencias e
           LEFT JOIN unidades u ON u.unit_number = e.unit_number
           LEFT JOIN asignaciones a ON a.id = e.asignacion_id
           WHERE e.tipo='video' OR LOWER(e.nombre_archivo) REGEXP %s
           ORDER BY e.unit_number, e.asignacion_id, e.id
           LIMIT 2000""",
        (_VIDEO_REGEX,),
    ) or []

    resumen = {"total": 0, "visibles": 0, "con_problema": 0,
               "base_de_datos": 0, "onedrive": 0, "PERDIDO": 0}
    unidades: dict = {}
    for r in rows:
        ev = _evaluar_video(r)
        resumen["total"] += 1
        resumen["visibles" if ev["visible"] else "con_problema"] += 1
        resumen[ev["ubicacion"]] += 1
        if solo_problemas and ev["visible"]:
            continue
        u = unidades.setdefault(r["unit_number"], {
            "unit_number": r["unit_number"], "id_lote": r.get("id_lote") or "",
            "unidad_existe": r.get("u_unit") is not None, "unidad_oculta": bool(r.get("u_oculto")),
            "tareas": {},
        })
        clave = r["asignacion_id"] if r["asignacion_id"] is not None else 0
        t = u["tareas"].setdefault(clave, {
            "asignacion_id": r["asignacion_id"], "actividad": r.get("actividad") or "",
            "estado": r.get("estado_tarea") or "", "videos": [],
        })
        t["videos"].append({
            "id": r["id"], "nombre": r["nombre_archivo"] or f"video_{r['id']}", "tecnico": r.get("tecnico") or "",
            "fecha": str(r["fecha"]) if r["fecha"] else "", "tipo": r.get("tipo") or "foto",
            "mb": round(float(r["bytes_db"]) / 1048576, 1) if r.get("bytes_db") else 0,
            **ev,
        })
    lista = []
    for u in unidades.values():
        u["tareas"] = list(u["tareas"].values())
        lista.append(u)
    return {"resumen": resumen, "unidades": lista}

# ── ¿OneDrive está funcionando? (token, espacio) — solo admin ──────────────
@router.get("/onedrive-estado")
def onedrive_estado(current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    if not ONEDRIVE_ENABLED:
        return {"ok": False, "paso": "importar", "error": "No se pudo cargar onedrive_service"}
    import onedrive_service as od
    try:
        od._cached_token["expires_at"] = 0          # forzar un token nuevo, sin usar la caché
        token = od._get_token()
    except Exception as e:
        return {"ok": False, "paso": "token", "error": str(e)[:400],
                "que_hacer": "Si dice invalid_grant/expired: hay que generar un MS_REFRESH_TOKEN nuevo. "
                             "Si dice invalid_client: el secreto de la app (MS_CLIENT_SECRET_PERSONAL) venció."}
    try:
        r = requests.get(f"{od.GRAPH_BASE}/me/drive?select=id,driveType,quota",
                         headers={"Authorization": f"Bearer {token}"}, timeout=20)
        if not r.ok:
            return {"ok": False, "paso": "graph", "http": r.status_code, "error": r.text[:300]}
        q = r.json().get("quota") or {}
        gb = lambda b: round((b or 0) / 1024 ** 3, 2)
        return {"ok": True, "estado_cuota": q.get("state"), "usado_gb": gb(q.get("used")),
                "total_gb": gb(q.get("total")), "libre_gb": gb(q.get("remaining"))}
    except Exception as e:
        return {"ok": False, "paso": "graph", "error": str(e)[:300]}


# ── RESUMEN POR ACTIVIDAD de una unidad: qué tarea tiene cuántas fotos/videos ──
@router.get("/resumen/{unit_number}")
def resumen_por_actividad(unit_number: str, current_user=Depends(require_admin_or_visor)):
    rows = execute_read(
        """SELECT e.asignacion_id AS asignacion_id, a.actividad_id AS actividad, a.tecnico AS tecnico_tarea,
                  SUM(CASE WHEN COALESCE(e.tipo,'foto')='video' THEN 1 ELSE 0 END) AS videos,
                  SUM(CASE WHEN COALESCE(e.tipo,'foto')<>'video' THEN 1 ELSE 0 END) AS fotos,
                  MAX(e.created_at) AS ultima
           FROM evidencias e
           LEFT JOIN asignaciones a ON a.id = e.asignacion_id
           WHERE e.unit_number=%s
           GROUP BY e.asignacion_id, a.actividad_id, a.tecnico
           ORDER BY MAX(e.created_at) DESC""",
        (unit_number,)
    )
    return [{
        "asignacion_id": r["asignacion_id"],
        "actividad": r["actividad"] or "Sin actividad",
        "tecnico": r["tecnico_tarea"] or "",
        "fotos": int(r["fotos"] or 0),
        "videos": int(r["videos"] or 0),
        "ultima": str(r["ultima"]) if r["ultima"] else "",
    } for r in (rows or [])]


# ── DESCARGAR LOS VIDEOS QUE VIVEN EN LA BASE DE DATOS — solo admin ─────────
# Rescate: saca TODOS los videos guardados en la DB (blob único o en partes),
# se vean o no en la app (unidad oculta/inexistente, sin tarea, guardados como
# 'foto', etc.). No depende de ninguna de esas reglas de visibilidad.
# Va por tandas (limite) para no agotar RAM ni topar con el timeout del gateway:
# cada llamada devuelve un ZIP y las cabeceras X-Siguiente-Desde / X-Pendientes
# dicen cómo pedir la siguiente. Estructura: Unidad / Tarea_<id>_<actividad> / archivo.
# Incluye LEEME.csv con unidad, tarea, técnico y fecha de cada video. Solo lectura.
def _seguro(txt, defecto="x"):
    t = re.sub(r"[^\w.\-]+", "_", str(txt or "")).strip("._")
    return (t or defecto)[:80]


@router.get("/descargar-videos")
def descargar_videos(desde_id: int = 0, limite: int = 20, unidad: Optional[str] = None,
                     current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    limite = max(1, min(int(limite), 50))
    filtro = ("(e.tipo='video' OR LOWER(e.nombre_archivo) REGEXP %s) "
              "AND (e.contenido IS NOT NULL OR EXISTS "
              "(SELECT 1 FROM evidencia_partes p WHERE p.evidencia_id = e.id)) AND e.id > %s")
    params = [_VIDEO_REGEX, desde_id]
    if unidad:
        filtro += " AND e.unit_number=%s"
        params.append(unidad)
    filas = execute_read(
        "SELECT e.id, e.unit_number, e.nombre_archivo, e.tecnico, e.asignacion_id, e.created_at, "
        "a.actividad_id AS actividad, LENGTH(e.contenido) AS bytes_db "
        f"FROM evidencias e LEFT JOIN asignaciones a ON a.id = e.asignacion_id WHERE {filtro} "
        "ORDER BY e.id LIMIT %s", tuple(params) + (limite,)
    ) or []
    if not filas:
        raise HTTPException(status_code=404, detail="No hay más videos en la base de datos")
    ultimo_id = filas[-1]["id"]
    restantes = execute_read(
        f"SELECT COUNT(*) AS n FROM evidencias e WHERE {filtro} AND e.id > %s", tuple(params) + (ultimo_id,)
    )
    pendientes = int(restantes[0]["n"]) if restantes else 0

    tmp = tempfile.NamedTemporaryFile(prefix="videos_db_", suffix=".zip", delete=False)
    tmp.close()
    manifiesto = [["id", "unidad", "tarea_id", "actividad", "tecnico", "fecha", "archivo_original", "bytes", "ruta_en_zip", "estado"]]
    try:
        with zipfile.ZipFile(tmp.name, "w", zipfile.ZIP_STORED, allowZip64=True) as zf:
            for r in filas:
                nombre = r["nombre_archivo"] or f"video_{r['id']}.mp4"
                carpeta = f"{_seguro(r['unit_number'], 'sin_unidad')}/" + (
                    f"Tarea_{r['asignacion_id']}_{_seguro(r['actividad'], 'sin_actividad')}"
                    if r["asignacion_id"] is not None else "Sin_tarea")
                ruta = f"{carpeta}/{r['id']}_{_seguro(nombre, 'video.mp4')}"
                try:
                    total_partes = 0 if r.get("bytes_db") else ep.tamano_total(r["id"])
                    if total_partes:                                    # archivo grande guardado en trozos
                        with zf.open(ruta, "w", force_zip64=True) as dest:
                            for trozo in ep.iterar_rango(r["id"], 0, total_partes - 1):
                                dest.write(trozo)
                        tam = total_partes
                    else:
                        fila = execute_read("SELECT contenido FROM evidencias WHERE id=%s", (r["id"],))
                        datos = bytes(fila[0]["contenido"]) if fila and fila[0]["contenido"] else b""
                        if not datos:
                            raise Exception("sin contenido")
                        zf.writestr(ruta, datos)
                        tam = len(datos)
                    estado = "ok"
                except Exception as e:
                    logger.error(f"[descargar-videos] id={r['id']}: {e}")
                    ruta, tam, estado = "", 0, f"ERROR: {str(e)[:80]}"
                manifiesto.append([r["id"], r["unit_number"], r["asignacion_id"] or "", r["actividad"] or "",
                                   r["tecnico"] or "", str(r["created_at"] or ""), nombre, tam, ruta, estado])
            buf = io.StringIO()
            csv.writer(buf).writerows(manifiesto)
            zf.writestr("LEEME.csv", "\ufeff" + buf.getvalue())      # BOM: Excel lo abre con acentos
    except Exception:
        try: os.remove(tmp.name)
        except OSError: pass
        raise
    return FileResponse(
        tmp.name, media_type="application/zip",
        filename=f"videos_base_de_datos_{filas[0]['id']}_a_{ultimo_id}.zip",
        headers={"X-Siguiente-Desde": str(ultimo_id), "X-Pendientes": str(pendientes),
                 "X-En-Esta-Tanda": str(len(filas)), "Access-Control-Expose-Headers": "X-Siguiente-Desde, X-Pendientes, X-En-Esta-Tanda"},
        background=BackgroundTask(lambda: os.path.exists(tmp.name) and os.remove(tmp.name)),
    )


# ── ESTADO DE SALUD de la evidencia (lo que ve el banner del panel) — solo admin ──
@router.get("/salud")
def salud_evidencias(ahora: bool = False, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    import salud_evidencias as sv
    estado = None if ahora else sv.leer_estado("evidencia")
    if estado is None:                       # aún no corrió el monitor, o se pidió revisar ya
        estado = sv.evaluar()
    return estado
