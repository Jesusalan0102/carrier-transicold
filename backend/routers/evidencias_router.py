from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Header
from fastapi.responses import StreamingResponse, Response
from fastapi.concurrency import run_in_threadpool
from auth import verify_token
from db import execute_read, execute_write
from typing import List, Optional
import zipfile
import io
import logging
import asyncio
from PIL import Image


def require_admin_or_visor(current_user=Depends(verify_token)):
    if current_user["role"] not in ("admin", "visor"):
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores y visores")
    return current_user

# ── Importación opcional de OneDrive ────────────────────────────────────────
try:
    from onedrive_service import sync_evidencia, sync_zip_evidencias
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
async def procesar_foto(file: UploadFile, unidad: str, tecnico: str, asignacion_id: int = None) -> dict:
    """Lee, comprime (si es foto) y guarda una foto o video. Devuelve
    {'filename', 'ok', 'error'}."""
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

        # execute_write es una llamada SÍNCRONA a MySQL; si se llama directo
        # dentro de un endpoint async bloquea TODO el event loop (la app corre
        # con 1 solo worker en Clever Cloud). Con varias fotos subiendo a la
        # vez esto acumula bloqueo suficiente para que el gateway corte la
        # conexión antes de recibir respuesta. Se ejecuta en threadpool para
        # no bloquear el loop mientras se escribe el BLOB en la base de datos.
        ok = await run_in_threadpool(
            execute_write,
            "INSERT INTO evidencias (unit_number, nombre_archivo, contenido, tecnico, asignacion_id, tipo, mime_type) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)",
            (unidad, file.filename, contenido, tecnico, asignacion_id, tipo, mime_type)
        )

        # OneDrive en background — no bloquea la respuesta al celular
        if ok and ONEDRIVE_ENABLED:
            asyncio.create_task(_sync_onedrive_bg(unidad, file.filename, contenido))

        return {"filename": file.filename, "ok": bool(ok), "error": None}
    except Exception as e:
        logger.error(f"[upload] Error procesando {file.filename}: {e}")
        return {"filename": file.filename, "ok": False, "error": str(e)}


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
        "SELECT COUNT(*) AS total FROM evidencias WHERE asignacion_id=%s",
        (asignacion_id,)
    )
    return {"total": res[0]["total"] if res else 0}


# ── LISTAR FOTOS DE UNA ACTIVIDAD ESPECÍFICA — solo admin/visor ──────────
@router.get("/por-actividad/{asignacion_id}")
def evidencias_por_actividad(asignacion_id: int, current_user=Depends(require_admin_or_visor)):
    rows = execute_read(
        """SELECT id, nombre_archivo, tecnico, unit_number, tipo,
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
        "unit_number": r["unit_number"],
        "tipo": r.get("tipo") or "foto",
        "fecha": str(r["fecha"]) if r["fecha"] else "",
    } for r in (rows or [])]
    return {"asignacion_id": asignacion_id, "total": len(fotos), "fotos": fotos}


# ── SUBIR FOTOS ───────────────────────────────────────────────────────────
@router.post("/upload")
async def subir_evidencias(
    unidad: str = Form(...),
    tecnico: str = Form(...),
    files: List[UploadFile] = File(...),
    asignacion_id: int = Form(None),
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

    # ── Procesar en paralelo con semáforo para no saturar DB/red ──────────
    semaforo = asyncio.Semaphore(MAX_CONCURRENT)

    async def procesar_con_limite(file):
        async with semaforo:
            return await procesar_foto(file, unidad, tecnico, asignacion_id)

    resultados = await asyncio.gather(
        *[procesar_con_limite(f) for f in files_a_guardar],
        return_exceptions=False
    )

    guardadas = sum(1 for r in resultados if r["ok"])
    fallidas  = [r["filename"] for r in resultados if not r["ok"]]

    respuesta = {
        "mensaje"  : f"{guardadas} foto(s) guardada(s)",
        "guardadas": guardadas,
        "total_enviadas": len(files_a_guardar),
    }
    if fallidas:
        respuesta["fallidas"] = fallidas
    if ONEDRIVE_ENABLED:
        respuesta["onedrive"] = "sincronización en segundo plano"

    return respuesta


# ── DESCARGAR ZIP DE TODAS LAS FOTOS DE UNA UNIDAD ───────────────────────
@router.get("/download/{unit_number}")
async def descargar_evidencias(unit_number: str, current_user=Depends(require_admin_or_visor)):
    meta = execute_read(
        "SELECT id, nombre_archivo FROM evidencias WHERE unit_number=%s",
        (unit_number,)
    )
    if not meta:
        raise HTTPException(status_code=404, detail="No hay evidencias para esta unidad")

    # Traer todos los contenidos en una sola query (evita N queries)
    ids = tuple(m["id"] for m in meta)
    placeholders = ",".join(["%s"] * len(ids))
    filas = execute_read(
        f"SELECT id, contenido FROM evidencias WHERE id IN ({placeholders})", ids
    )
    contenidos = {f["id"]: f["contenido"] for f in filas if f["contenido"]}

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
        nombres_vistos = {}
        for m in meta:
            contenido = contenidos.get(m["id"])
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
    current_user=Depends(require_admin_or_visor)
):
    offset = (page - 1) * per_page
    total_res = execute_read(
        "SELECT COUNT(*) AS total FROM evidencias WHERE unit_number=%s",
        (unit_number,)
    )
    total = total_res[0]["total"] if total_res else 0

    rows = execute_read(
        """SELECT e.id, e.nombre_archivo, e.tecnico, e.asignacion_id, e.tipo,
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
            "tipo": r.get("tipo") or "foto",
            "fecha": str(r["fecha"]) if r["fecha"] else "",
            "actividad": r.get("actividad") or "",
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
        """SELECT e.unit_number AS unit_number, COUNT(*) AS total, u.id_lote AS id_lote
           FROM evidencias e
           INNER JOIN unidades u ON u.unit_number = e.unit_number
           WHERE u.oculto = 0
           GROUP BY e.unit_number, u.id_lote
           ORDER BY u.id_lote, e.unit_number"""
    )
    return [{"unit_number": r["unit_number"], "total": r["total"], "id_lote": r["id_lote"]} for r in (rows or [])]


# ── SERVIR UNA FOTO O VIDEO INDIVIDUAL — solo admin/visor ─────────────────
@router.get("/foto/{foto_id}")
def ver_foto(foto_id: int, range: Optional[str] = Header(None), current_user=Depends(require_admin_or_visor)):
    rows = execute_read(
        "SELECT nombre_archivo, contenido, mime_type, tipo FROM evidencias WHERE id=%s",
        (foto_id,)
    )
    if not rows or not rows[0]["contenido"]:
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    contenido = rows[0]["contenido"]
    contenido = bytes(contenido) if not isinstance(contenido, bytes) else contenido
    nombre = rows[0]["nombre_archivo"] or "foto.jpg"
    ext = _extension(nombre)
    media_type = rows[0].get("mime_type") or MIME_MAP.get(ext, "application/octet-stream")
    es_video = (rows[0].get("tipo") == "video")

    if not es_video:
        return Response(
            content=contenido,
            media_type=media_type,
            headers={"Cache-Control": "private, max-age=3600"},
        )

    # ── Video: soporta Range requests para que el navegador pueda hacer
    # streaming/seek en vez de tener que bajar el archivo completo primero ─
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
    execute_write(
        f"DELETE FROM evidencias WHERE id IN ({placeholders})", tuple(ids)
    )
    return {"mensaje": f"{len(ids)} foto(s) eliminada(s)", "ids": ids}
