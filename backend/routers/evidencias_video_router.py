"""
Subida de VIDEO de evidencia por partes (reanudable e idempotente).

Flujo:
  1. POST /api/evidencias/video/iniciar        -> abre (o reanuda) una sesión en OneDrive
  2. PUT  /api/evidencias/video/{id}/parte     -> manda un trozo (X-Offset); repetir hasta done
  3. GET  /api/evidencias/video/{id}/estado    -> dónde quedó (para reanudar tras un corte)

Garantías:
  - Nunca hay un video completo en RAM: solo un trozo (~3.75 MB) a la vez.
  - Si se corta la señal / se cierra la app, se continúa desde el último byte confirmado.
  - client_id hace la subida idempotente: reintentar jamás duplica el video.
  - La fila de `evidencias` se crea SOLO cuando OneDrive confirmó el archivo completo,
    y se puede recuperar aunque se pierda la respuesta del último trozo.
"""
import logging
import re
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from auth import verify_token
from db import execute_read, execute_write

try:
    import onedrive_service as od
    ONEDRIVE_ENABLED = True
except ImportError:  # pragma: no cover
    od = None
    ONEDRIVE_ENABLED = False

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/evidencias/video", tags=["evidencias-video"])

VIDEO_EXTENSIONS = {"mp4", "mov", "webm", "m4v", "3gp", "avi", "mkv"}
MIME_MAP = {
    "mp4": "video/mp4", "mov": "video/quicktime", "webm": "video/webm",
    "m4v": "video/x-m4v", "3gp": "video/3gpp", "avi": "video/x-msvideo", "mkv": "video/x-matroska",
}
MAX_VIDEO_BYTES = 300 * 1024 * 1024   # al subir por partes ya no depende de la RAM del servidor
MAX_EVIDENCIAS_POR_ACTIVIDAD = 100


class IniciarVideo(BaseModel):
    client_id: str
    unidad: str
    asignacion_id: Optional[int] = None
    nombre: str
    tamano: int
    mime: Optional[str] = None
    equipo: Optional[str] = None


def _chunk() -> int:
    return od.VIDEO_CHUNK_BYTES


def _ext(nombre: str) -> str:
    return nombre.rsplit(".", 1)[-1].lower() if nombre and "." in nombre else ""


def _nombre_unico(nombre: str, asignacion_id) -> str:
    base = re.sub(r"[^\w.\-]", "_", nombre or "video.mp4")[:120]
    return f"A{asignacion_id or 0}_{uuid.uuid4().hex[:8]}_{base}"


def _normalizar_equipo(tecnico: str, equipo: Optional[str]) -> Optional[str]:
    if not equipo:
        return None
    vistos, ordenados = set(), []
    for n in [tecnico] + [x.strip() for x in equipo.split(",") if x.strip()]:
        if n not in vistos:
            vistos.add(n)
            ordenados.append(n)
    return ", ".join(ordenados) if len(ordenados) > 1 else None


def _get_row(upload_id: str, usuario: str):
    rows = execute_read("SELECT * FROM video_uploads WHERE upload_id=%s", (upload_id,))
    if not rows or rows[0]["tecnico"] != usuario:
        raise HTTPException(status_code=404, detail="Sesión de subida no encontrada")
    return rows[0]


def _registrar_evidencia(row: dict, item: dict) -> int:
    """Crea la fila en `evidencias` UNA sola vez (idempotente ante reintentos concurrentes)."""
    # Reclamo atómico: solo una petición pasa de NULL -> 0.
    reclamada = execute_write(
        "UPDATE video_uploads SET evidencia_id=0 WHERE upload_id=%s AND evidencia_id IS NULL",
        (row["upload_id"],),
    )
    if not reclamada:
        actual = execute_read("SELECT evidencia_id FROM video_uploads WHERE upload_id=%s", (row["upload_id"],))
        eid = actual[0]["evidencia_id"] if actual else None
        if eid:
            return eid
        raise HTTPException(status_code=503, detail="Guardando el video, reintenta en unos segundos")
    try:
        from db import execute_write_with_id
        eid = execute_write_with_id(
            "INSERT INTO evidencias (unit_number, nombre_archivo, contenido, tecnico, asignacion_id, "
            "tipo, mime_type, onedrive_item_id, onedrive_url, equipo) "
            "VALUES (%s,%s,NULL,%s,%s,'video',%s,%s,%s,%s)",
            (row["unidad"], row["nombre_archivo"], row["tecnico"], row["asignacion_id"],
             row["mime_type"], item.get("id"), item.get("webUrl"), row["equipo"]),
        )
        execute_write("UPDATE video_uploads SET evidencia_id=%s WHERE upload_id=%s", (eid, row["upload_id"]))
        return eid
    except Exception:
        # Liberar el reclamo para que el reintento del celular vuelva a intentarlo.
        execute_write("UPDATE video_uploads SET evidencia_id=NULL WHERE upload_id=%s", (row["upload_id"],))
        raise


def _recuperar_si_ya_esta_en_onedrive(row: dict) -> Optional[int]:
    """Si la sesión ya no existe pero el archivo completo sí está en OneDrive
    (se perdió la respuesta del último trozo), se registra sin volver a subirlo."""
    item = od.buscar_item_por_ruta(row["onedrive_path"])
    if item and int(item.get("size") or 0) == int(row["tamano"]):
        return _registrar_evidencia(row, item)
    return None


@router.post("/iniciar")
async def iniciar(data: IniciarVideo, current_user=Depends(verify_token)):
    if not ONEDRIVE_ENABLED:
        raise HTTPException(status_code=503, detail="Subida por partes no disponible")
    usuario = current_user["username"]
    ext = _ext(data.nombre)
    if ext not in VIDEO_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Formato de video no permitido")
    if data.tamano <= 0:
        raise HTTPException(status_code=400, detail="El video está vacío")
    if data.tamano > MAX_VIDEO_BYTES:
        mb = MAX_VIDEO_BYTES // (1024 * 1024)
        raise HTTPException(status_code=400, detail=f"El video pesa más de {mb}MB. Recórtalo o baja la calidad.")
    if not data.client_id or len(data.client_id) > 120:
        raise HTTPException(status_code=400, detail="client_id inválido")

    existente = await run_in_threadpool(
        execute_read, "SELECT * FROM video_uploads WHERE tecnico=%s AND client_id=%s", (usuario, data.client_id)
    )
    if existente:
        row = existente[0]
        if row["evidencia_id"]:
            return {"done": True, "evidencia_id": row["evidencia_id"], "upload_id": row["upload_id"]}
        try:
            siguiente = await run_in_threadpool(od.estado_sesion_video, row["upload_url"])
        except Exception as e:
            logger.warning(f"[video] estado de sesión falló al reanudar: {e}")
            raise HTTPException(status_code=502, detail="No se pudo consultar la sesión de subida")
        if siguiente is not None:
            return {"done": False, "upload_id": row["upload_id"], "next_start": siguiente, "chunk_size": _chunk()}
        # La sesión expiró: ¿el archivo ya había quedado completo?
        eid = await run_in_threadpool(_recuperar_si_ya_esta_en_onedrive, row)
        if eid:
            return {"done": True, "evidencia_id": eid, "upload_id": row["upload_id"]}
        # Abrir sesión nueva sobre la misma fila.
        try:
            nueva = await run_in_threadpool(od.crear_sesion_video, row["onedrive_path"])
        except Exception as e:
            logger.error(f"[video] no se pudo recrear la sesión: {e}")
            raise HTTPException(status_code=502, detail="OneDrive no respondió, reintenta")
        await run_in_threadpool(
            execute_write, "UPDATE video_uploads SET upload_url=%s WHERE upload_id=%s", (nueva, row["upload_id"])
        )
        return {"done": False, "upload_id": row["upload_id"], "next_start": 0, "chunk_size": _chunk()}

    # Límite por actividad (evidencias ya guardadas + videos en curso no cuentan hasta terminar)
    if data.asignacion_id is not None:
        res = await run_in_threadpool(
            execute_read, "SELECT COUNT(*) AS total FROM evidencias WHERE asignacion_id=%s", (data.asignacion_id,)
        )
        if res and res[0]["total"] >= MAX_EVIDENCIAS_POR_ACTIVIDAD:
            raise HTTPException(
                status_code=400,
                detail=f"Ya alcanzaste el límite de {MAX_EVIDENCIAS_POR_ACTIVIDAD} archivos para esta actividad",
            )

    try:
        carpeta = await run_in_threadpool(od.carpeta_evidencia_unidad, data.unidad)
        ruta = f"{carpeta}/{_nombre_unico(data.nombre, data.asignacion_id)}"
        upload_url = await run_in_threadpool(od.crear_sesion_video, ruta)
    except Exception as e:
        # OneDrive caído / token vencido: 503 hace que la app use el método clásico, que
        # guarda el video en la base de datos como respaldo. El video nunca se queda sin guardar.
        logger.error(f"[video] no se pudo abrir sesión en OneDrive, se usará respaldo en DB: {e}")
        raise HTTPException(status_code=503, detail="OneDrive no disponible; se guardará de forma directa")

    upload_id = str(uuid.uuid4())
    mime = MIME_MAP.get(ext) or data.mime or "application/octet-stream"
    try:
        await run_in_threadpool(
            execute_write,
            "INSERT INTO video_uploads (upload_id, client_id, tecnico, unidad, asignacion_id, equipo, "
            "nombre_archivo, mime_type, tamano, onedrive_path, upload_url) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (upload_id, data.client_id, usuario, data.unidad, data.asignacion_id,
             _normalizar_equipo(usuario, data.equipo), data.nombre[:255], mime, data.tamano, ruta, upload_url),
        )
    except Exception as e:
        # Carrera: dos "iniciar" simultáneos con el mismo client_id -> se queda con el que ganó.
        otra = await run_in_threadpool(
            execute_read, "SELECT * FROM video_uploads WHERE tecnico=%s AND client_id=%s", (usuario, data.client_id)
        )
        if otra:
            return {"done": bool(otra[0]["evidencia_id"]), "evidencia_id": otra[0]["evidencia_id"] or None,
                    "upload_id": otra[0]["upload_id"], "next_start": 0, "chunk_size": _chunk()}
        logger.error(f"[video] no se pudo registrar la sesión: {e}")
        raise HTTPException(status_code=500, detail="No se pudo preparar la subida")
    return {"done": False, "upload_id": upload_id, "next_start": 0, "chunk_size": _chunk()}


@router.put("/{upload_id}/parte")
async def subir_parte(upload_id: str, request: Request, current_user=Depends(verify_token)):
    usuario = current_user["username"]
    row = await run_in_threadpool(_get_row, upload_id, usuario)
    if row["evidencia_id"]:
        return {"done": True, "evidencia_id": row["evidencia_id"]}

    try:
        offset = int(request.headers.get("x-offset", ""))
    except ValueError:
        raise HTTPException(status_code=400, detail="Falta el encabezado X-Offset")
    data = await request.body()
    total = int(row["tamano"])
    if not data or offset < 0 or offset + len(data) > total:
        raise HTTPException(status_code=400, detail="Parte fuera de rango")
    es_ultima = offset + len(data) == total
    if not es_ultima and len(data) % (320 * 1024) != 0:
        raise HTTPException(status_code=400, detail="Tamaño de parte inválido")

    try:
        resp = await run_in_threadpool(od.subir_parte_video, row["upload_url"], offset, data, total)
    except Exception as e:
        logger.warning(f"[video] fallo de red hacia OneDrive en {upload_id}@{offset}: {e}")
        raise HTTPException(status_code=502, detail="Conexión con OneDrive interrumpida, reintenta")

    code = resp.status_code
    if code == 202:
        siguiente = offset + len(data)
        try:
            rangos = resp.json().get("nextExpectedRanges") or []
            if rangos:
                siguiente = int(str(rangos[0]).split("-")[0])
        except Exception:
            pass
        return {"done": False, "next_start": siguiente}

    if code in (200, 201):
        item = resp.json()
        eid = await run_in_threadpool(_registrar_evidencia, row, item)
        logger.info(f"[video] subida completa {row['nombre_archivo']} -> evidencia {eid}")
        return {"done": True, "evidencia_id": eid}

    # Sesión caducada, o el trozo ya se había recibido (se perdió la respuesta anterior).
    if code in (404, 409, 410, 416):
        try:
            siguiente = await run_in_threadpool(od.estado_sesion_video, row["upload_url"])
        except Exception:
            siguiente = None
        if siguiente is not None:
            return {"done": False, "next_start": siguiente}
        try:
            eid = await run_in_threadpool(_recuperar_si_ya_esta_en_onedrive, row)
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"[video] no se pudo verificar en OneDrive: {e}")
            eid = None
        if eid:
            return {"done": True, "evidencia_id": eid}
        # Sesión perdida de verdad: el cliente debe llamar a /iniciar otra vez (con el mismo client_id).
        raise HTTPException(status_code=410, detail="La sesión de subida expiró; se reiniciará")

    logger.error(f"[video] OneDrive respondió {code} en {upload_id}@{offset}: {resp.text[:200]}")
    raise HTTPException(status_code=502, detail=f"OneDrive respondió {code}, reintenta")


@router.get("/{upload_id}/estado")
async def estado(upload_id: str, current_user=Depends(verify_token)):
    row = await run_in_threadpool(_get_row, upload_id, current_user["username"])
    if row["evidencia_id"]:
        return {"done": True, "evidencia_id": row["evidencia_id"]}
    try:
        siguiente = await run_in_threadpool(od.estado_sesion_video, row["upload_url"])
    except Exception:
        raise HTTPException(status_code=502, detail="No se pudo consultar OneDrive")
    if siguiente is None:
        eid = await run_in_threadpool(_recuperar_si_ya_esta_en_onedrive, row)
        if eid:
            return {"done": True, "evidencia_id": eid}
        raise HTTPException(status_code=410, detail="La sesión de subida expiró")
    return {"done": False, "next_start": siguiente}
