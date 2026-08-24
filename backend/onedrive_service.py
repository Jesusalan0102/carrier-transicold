"""
onedrive_service.py
-------------------
Módulo para sincronizar archivos con OneDrive Personal via Microsoft Graph API.
Usa refresh token (OAuth) para autenticación sin login manual continuo.

MEJORAS v2:
  - Token cacheado con expiración (ya no pide token por cada archivo)
  - Subida con reintentos automáticos (3 intentos con backoff)
  - Subida paralela en lotes (ThreadPoolExecutor)

Variables de entorno requeridas (.env / Render):
  MS_CLIENT_ID_PERSONAL     → App Registration carrier-onedrive-personal > Application ID
  MS_CLIENT_SECRET_PERSONAL → Secreto de carrier-onedrive-personal
  MS_REFRESH_TOKEN          → Refresh token obtenido via OAuth
"""

import os
import time
import logging
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

TZ = ZoneInfo("America/Tijuana")

BASE_FOLDER    = "carrier-transicold"
EVIDENCIAS_DIR = f"{BASE_FOLDER}/Evidencias"
REPORTES_DIR   = f"{BASE_FOLDER}/Reportes"
GRAPH_BASE     = "https://graph.microsoft.com/v1.0"

# ── Cache del token con expiración ──────────────────────────────────────────
# FIX: antes se pedía un token nuevo por cada archivo subido.
# Ahora se reutiliza el mismo token hasta 5 min antes de que expire.
_cached_token = {"value": None, "expires_at": 0}


def _get_token() -> str:
    """Obtiene access token usando el refresh token. Reutiliza el token en caché."""
    now = time.time()
    # Reutilizar token si le quedan más de 5 minutos de vida
    if _cached_token["value"] and now < _cached_token["expires_at"] - 300:
        return _cached_token["value"]

    client_id     = os.getenv("MS_CLIENT_ID_PERSONAL")
    client_secret = os.getenv("MS_CLIENT_SECRET_PERSONAL")
    refresh_token = os.getenv("MS_REFRESH_TOKEN")

    if not all([client_id, client_secret, refresh_token]):
        raise EnvironmentError(
            "Faltan variables: MS_CLIENT_ID_PERSONAL, MS_CLIENT_SECRET_PERSONAL, MS_REFRESH_TOKEN"
        )

    resp = requests.post(
        "https://login.microsoftonline.com/common/oauth2/v2.0/token",
        data={
            "client_id":     client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type":    "refresh_token",
            "scope":         "https://graph.microsoft.com/Files.ReadWrite offline_access User.Read",
        },
        timeout=30,
    )
    data = resp.json()
    if "access_token" not in data:
        raise Exception(f"Error obteniendo token: {data.get('error_description', data)}")

    expires_in = data.get("expires_in", 3600)
    _cached_token["value"]      = data["access_token"]
    _cached_token["expires_at"] = now + expires_in
    return data["access_token"]


def _upload_with_retry(fn, *args, max_retries: int = 3, **kwargs):
    """
    FIX: Ejecuta una función de subida con reintentos automáticos.
    Antes, un solo fallo de red dejaba todas las fotos siguientes sin subir.
    Ahora reintenta hasta 3 veces con espera exponencial (2s, 4s, 8s).
    """
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt < max_retries:
                wait = 2 ** attempt
                logger.warning(f"[OneDrive] Intento {attempt} fallido, reintentando en {wait}s... ({e})")
                time.sleep(wait)
            else:
                logger.error(f"[OneDrive] Todos los intentos fallaron: {e}")
    raise last_error


def _sanitize_folder_name(name: str) -> str:
    """
    Elimina caracteres prohibidos por OneDrive/SharePoint en nombres de carpeta.
    Prohibidos: ~ " # % & * : < > ? / \\ { | }
    También elimina puntos y espacios al inicio/final (regla de OneDrive).
    """
    forbidden = set('~"#%&*:<>?/\\{|}')
    sanitized = "".join(c for c in name if c not in forbidden)
    return sanitized.strip(". ")


def _ensure_folder(folder_path: str) -> str:
    """
    Garantiza que la carpeta (y toda su jerarquía) exista en OneDrive.
    Devuelve el path final (sanitizado) de la carpeta.

    La Graph API NO crea carpetas intermedias al hacer PUT de un archivo:
    si la carpeta no existe, el upload falla con 404.
    Este helper lo resuelve recorriendo cada nivel del path.

    Fixes aplicados:
    - conflictBehavior cambiado de "rename" a "fail":
      "rename" creaba silenciosamente "carpeta 1" en lugar de "carpeta",
      causando que el upload posterior fallara con 404 porque el path
      real en OneDrive era distinto al que se intentaba escribir.
      Con "fail" + manejo de 409 tratamos el conflicto como "ya existe".
    - Sanitización de nombres: OneDrive prohíbe ~ " # % & * : < > ? / \\ { | }
      en nombres de carpeta; sin sanitizar, el POST de creación falla con 400.
    - Token se refresca en cada iteración (no se captura una vez al inicio)
      para evitar expiración en rutas con muchos niveles.
    """
    parts = [p for p in folder_path.strip("/").split("/") if p]
    current_path = ""

    for part in parts:
        part = _sanitize_folder_name(part)
        if not part:
            continue
        current_path = f"{current_path}/{part}" if current_path else part

        # Refrescar token en cada nivel (evita expiración a mitad del loop)
        headers = {
            "Authorization": f"Bearer {_get_token()}",
            "Content-Type": "application/json",
        }
        url = f"{GRAPH_BASE}/me/drive/root:/{current_path}"

        # Comprobar si ya existe como carpeta
        check = requests.get(url, headers=headers, timeout=15)
        if check.status_code == 200:
            item = check.json()
            if "folder" in item:
                continue  # es carpeta y ya existe → OK
            # Existe pero es un archivo con ese nombre — poco probable pero manejarlo
            raise Exception(
                f"'{current_path}' existe en OneDrive pero es un archivo, no una carpeta"
            )

        # No existe → crearla en el padre
        if current_path == part:
            parent_url = f"{GRAPH_BASE}/me/drive/root/children"
        else:
            parent_path = "/".join(current_path.split("/")[:-1])
            parent_url = f"{GRAPH_BASE}/me/drive/root:/{parent_path}:/children"

        body = {
            "name": part,
            "folder": {},
            # FIX: "rename" creaba "carpeta 1" silenciosamente → usar "fail" y
            # tratar 409 como "ya existe" (race condition entre workers concurrentes)
            "@microsoft.graph.conflictBehavior": "fail",
        }
        create_resp = requests.post(parent_url, headers=headers, json=body, timeout=15)

        if create_resp.status_code in (200, 201):
            logger.info(f"[OneDrive] Carpeta creada: {current_path}")
        elif create_resp.status_code == 409:
            # Conflicto = la carpeta ya existe (creada por otro worker concurrente)
            logger.debug(f"[OneDrive] Carpeta ya existe (409): {current_path}")
        else:
            raise Exception(
                f"No se pudo crear carpeta '{current_path}': "
                f"{create_resp.status_code} {create_resp.text[:300]}"
            )

    return current_path


def upload_bytes(content: bytes, onedrive_path: str, content_type: str = "application/octet-stream") -> dict:
    """Sube bytes a OneDrive personal (archivos hasta 4MB)."""
    url = f"{GRAPH_BASE}/me/drive/root:/{onedrive_path}:/content"
    resp = requests.put(
        url,
        headers={"Authorization": f"Bearer {_get_token()}", "Content-Type": content_type},
        data=content,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def upload_large_file(content: bytes, onedrive_path: str, content_type: str = "application/octet-stream") -> dict:
    """Sube archivos grandes (>4MB) usando Upload Session."""
    session_url = f"{GRAPH_BASE}/me/drive/root:/{onedrive_path}:/createUploadSession"
    session_resp = requests.post(
        session_url,
        headers={"Authorization": f"Bearer {_get_token()}", "Content-Type": "application/json"},
        json={"item": {"@microsoft.graph.conflictBehavior": "replace"}},
        timeout=30,
    )
    session_resp.raise_for_status()
    upload_url = session_resp.json()["uploadUrl"]

    chunk_size = 5 * 1024 * 1024
    file_size  = len(content)
    result     = {}
    for start in range(0, file_size, chunk_size):
        end   = min(start + chunk_size - 1, file_size - 1)
        chunk = content[start : end + 1]
        headers = {
            "Content-Length": str(len(chunk)),
            "Content-Range":  f"bytes {start}-{end}/{file_size}",
            "Content-Type":   content_type,
        }
        r = requests.put(upload_url, headers=headers, data=chunk, timeout=60)
        r.raise_for_status()
        result = r.json() if r.content else result
    return result


def get_download_url(item_id: str) -> str:
    """Obtiene una URL de descarga directa y temporal (~1h) para un item de
    OneDrive por su ID. Útil para servir video en streaming (soporta Range
    de forma nativa en la CDN de Microsoft) sin pasar el archivo por
    nuestro propio backend."""
    url = f"{GRAPH_BASE}/me/drive/items/{item_id}?select=id,@microsoft.graph.downloadUrl"
    resp = requests.get(
        url, headers={"Authorization": f"Bearer {_get_token()}"}, timeout=15
    )
    resp.raise_for_status()
    data = resp.json()
    return data.get("@microsoft.graph.downloadUrl", "")


def download_item_bytes(item_id: str) -> bytes:
    """Descarga el contenido completo de un item de OneDrive (para incluirlo
    en el ZIP de evidencias, ya que ese archivo no vive en la DB)."""
    download_url = get_download_url(item_id)
    if not download_url:
        raise Exception("No se pudo obtener la URL de descarga de OneDrive")
    resp = requests.get(download_url, timeout=120)
    resp.raise_for_status()
    return resp.content


def sync_reporte_ticket(ticket_num: int, nombre_archivo: str, contenido: bytes) -> dict:
    """
    Sube el reporte final (Word/PDF) que el técnico adjunta al cerrar un
    ticket. Se guarda en:
      carrier-transicold/Reportes/Tickets/Ticket_<num>_<nombre_original>

    Devuelve {'webUrl', 'item_id'} para guardarlos en tickets.reporte_archivo_*.
    """
    folder_path = f"{REPORTES_DIR}/Tickets"
    real_folder_path = _upload_with_retry(_ensure_folder, folder_path)

    ext = nombre_archivo.rsplit(".", 1)[-1].lower() if "." in nombre_archivo else ""
    mime_map = {
        "pdf":  "application/pdf",
        "doc":  "application/msword",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
    content_type = mime_map.get(ext, "application/octet-stream")
    file_path = f"{real_folder_path}/Ticket_{ticket_num}_{nombre_archivo}"

    uploader = upload_large_file if len(contenido) > 4 * 1024 * 1024 else upload_bytes
    result = _upload_with_retry(uploader, contenido, file_path, content_type)
    web_url = result.get("webUrl", "")
    item_id = result.get("id", "")
    logger.info(f"[OneDrive] Reporte de ticket subido: {file_path} (id={item_id})")
    return {"webUrl": web_url, "item_id": item_id}


def sync_video_evidencia(unit_number: str, nombre_archivo: str, contenido: bytes, unit_meta: dict = None) -> dict:
    """
    Sube un VIDEO de evidencia a OneDrive y devuelve {'webUrl', 'item_id'}.
    A diferencia de sync_evidencia (fotos), esta función se llama de forma
    SÍNCRONA antes de guardar la fila en la DB, porque para video no se
    guarda el blob completo en la base de datos -- solo la referencia --
    así que necesitamos confirmar que la subida a OneDrive funcionó antes
    de decidir qué guardar.

    Misma estructura de carpetas que las fotos:
      carrier-transicold/Evidencias/<id_lote>/<unit_number>_<reefer_serial>/
    """
    if unit_meta is None:
        try:
            from db import execute_read
            rows = execute_read(
                "SELECT id_lote, reefer_serial FROM unidades WHERE unit_number=%s LIMIT 1",
                (unit_number,)
            )
            unit_meta = rows[0] if rows else {}
        except Exception as e:
            logger.warning(f"[OneDrive] No se pudo obtener metadata de unidad {unit_number}: {e}")
            unit_meta = {}

    id_lote       = (unit_meta.get("id_lote") or "").strip()
    reefer_serial = (unit_meta.get("reefer_serial") or "").strip()
    subfolder_name = f"{unit_number}_{reefer_serial}" if reefer_serial else unit_number
    folder_path = f"{EVIDENCIAS_DIR}/{id_lote}/{subfolder_name}" if id_lote else f"{EVIDENCIAS_DIR}/{subfolder_name}"

    real_folder_path = _upload_with_retry(_ensure_folder, folder_path)

    ext = nombre_archivo.rsplit(".", 1)[-1].lower() if "." in nombre_archivo else "mp4"
    video_mime_map = {
        "mp4": "video/mp4", "mov": "video/quicktime", "webm": "video/webm",
        "m4v": "video/x-m4v", "3gp": "video/3gpp", "avi": "video/x-msvideo", "mkv": "video/x-matroska",
    }
    content_type = video_mime_map.get(ext, "application/octet-stream")
    file_path = f"{real_folder_path}/{nombre_archivo}"

    # Videos casi siempre superan los 4MB del upload simple -> sesión de subida
    result = _upload_with_retry(upload_large_file, contenido, file_path, content_type)
    web_url = result.get("webUrl", "")
    item_id = result.get("id", "")
    logger.info(f"[OneDrive] Video subido: {file_path} (id={item_id})")
    return {"webUrl": web_url, "item_id": item_id}


def sync_evidencia(unit_number: str, nombre_archivo: str, contenido: bytes, unit_meta: dict = None) -> str:
    """
    Sube una foto de evidencia a OneDrive.

    Estructura de carpetas:
      carrier-transicold/Evidencias/<id_lote>/<unit_number>_<reefer_serial>/

    Si unit_meta es None, consulta la DB para obtener id_lote y reefer_serial.
    Si la unidad no tiene esos datos, usa solo unit_number como nombre de carpeta.

    Crea la jerarquía de carpetas si no existe antes de subir el archivo.
    Incluye reintentos automáticos.
    """
    # ── 1. Obtener metadata de la unidad ──────────────────────────────────
    if unit_meta is None:
        try:
            from db import execute_read
            rows = execute_read(
                "SELECT id_lote, reefer_serial FROM unidades WHERE unit_number=%s LIMIT 1",
                (unit_number,)
            )
            unit_meta = rows[0] if rows else {}
        except Exception as e:
            logger.warning(f"[OneDrive] No se pudo obtener metadata de unidad {unit_number}: {e}")
            unit_meta = {}

    id_lote       = (unit_meta.get("id_lote") or "").strip()
    reefer_serial = (unit_meta.get("reefer_serial") or "").strip()

    # ── 2. Construir ruta de carpeta ──────────────────────────────────────
    # Nombre de subcarpeta: "<unit_number>_<reefer_serial>" o solo "<unit_number>"
    #
    # IMPORTANTE: se usa reefer_serial (no reefer_model) porque es un dato
    # inmutable una vez capturado. Antes se usaba reefer_model, que puede
    # estar vacío al subir la primera foto y llenarse después al editar la
    # unidad — eso generaba una carpeta NUEVA con nombre distinto para la
    # misma unidad cada vez que cambiaba el modelo, duplicando carpetas.
    # Con reefer_serial el path siempre resuelve igual para la misma unidad.
    subfolder_name = f"{unit_number}_{reefer_serial}" if reefer_serial else unit_number

    if id_lote:
        folder_path = f"{EVIDENCIAS_DIR}/{id_lote}/{subfolder_name}"
    else:
        folder_path = f"{EVIDENCIAS_DIR}/{subfolder_name}"

    # ── 3. Garantizar que la carpeta existe en OneDrive ───────────────────
    # IMPORTANTE: usar el path sanitizado que devuelve _ensure_folder,
    # porque los nombres de carpeta se sanitizan internamente y el path
    # real en OneDrive puede diferir del folder_path construido arriba.
    try:
        real_folder_path = _upload_with_retry(_ensure_folder, folder_path)
    except Exception as e:
        logger.error(f"[OneDrive] No se pudo crear carpeta '{folder_path}': {e}")
        raise

    # ── 4. Subir el archivo ───────────────────────────────────────────────
    ext = nombre_archivo.rsplit(".", 1)[-1].lower() if "." in nombre_archivo else "jpg"
    mime_map = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "png": "image/png",  "gif": "image/gif",
        "webp": "image/webp", "pdf": "application/pdf",
        "mp4": "video/mp4", "mov": "video/quicktime", "webm": "video/webm",
        "m4v": "video/x-m4v", "3gp": "video/3gpp", "avi": "video/x-msvideo", "mkv": "video/x-matroska",
    }
    content_type = mime_map.get(ext, "application/octet-stream")
    file_path = f"{real_folder_path}/{nombre_archivo}"

    try:
        result  = _upload_with_retry(upload_bytes, contenido, file_path, content_type)
        web_url = result.get("webUrl", "")
        logger.info(f"[OneDrive] Evidencia subida: {file_path}")
        return web_url
    except Exception as e:
        logger.error(f"[OneDrive] Error subiendo evidencia {file_path}: {e}")
        raise


def sync_evidencias_lote(unit_number: str, archivos: list[tuple[str, bytes]], max_workers: int = 4) -> dict:
    """
    Sube múltiples evidencias en paralelo usando hilos.
    Consulta la DB una sola vez para obtener metadata de la unidad
    y la pasa a cada llamada individual (evita N consultas a la DB).
    """
    try:
        from db import execute_read
        rows = execute_read(
            "SELECT id_lote, reefer_serial FROM unidades WHERE unit_number=%s LIMIT 1",
            (unit_number,)
        )
        unit_meta = rows[0] if rows else {}
    except Exception:
        unit_meta = {}

    subidas = []
    errores = []

    def _subir_uno(nombre, contenido):
        return sync_evidencia(unit_number, nombre, contenido, unit_meta=unit_meta)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_nombre = {
            executor.submit(_subir_uno, nombre, contenido): nombre
            for nombre, contenido in archivos
        }
        for future in as_completed(future_to_nombre):
            nombre = future_to_nombre[future]
            try:
                url = future.result()
                subidas.append({"archivo": nombre, "url": url})
            except Exception as e:
                logger.error(f"[OneDrive] Fallo en lote para {nombre}: {e}")
                errores.append({"archivo": nombre, "error": str(e)})

    return {"subidas": subidas, "errores": errores}


def sync_reporte_maestro(excel_bytes: bytes, fecha: str = None) -> str:
    """
    Sube el reporte Excel a:
      carrier-transicold/Reportes/YYYY-MM/Carrier_Reporte_YYYY-MM-DD.xlsx
    """
    if not fecha:
        fecha = datetime.now(TZ).strftime("%Y-%m-%d")
    mes    = fecha[:7]
    nombre = f"Carrier_Reporte_{fecha}.xlsx"
    path   = f"{REPORTES_DIR}/{mes}/{nombre}"
    mime   = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    try:
        result  = _upload_with_retry(upload_large_file, excel_bytes, path, mime)
        web_url = result.get("webUrl", "")
        logger.info(f"[OneDrive] Reporte subido: {path}")
        return web_url
    except Exception as e:
        logger.error(f"[OneDrive] Error subiendo reporte {path}: {e}")
        raise


def sync_zip_evidencias(unit_number: str, zip_bytes: bytes) -> str:
    """
    Sube el ZIP de evidencias de una unidad a la misma carpeta enriquecida:
      carrier-transicold/Evidencias/<id_lote>/<unit_number>_<reefer_serial>/
    """
    try:
        from db import execute_read
        rows = execute_read(
            "SELECT id_lote, reefer_serial FROM unidades WHERE unit_number=%s LIMIT 1",
            (unit_number,)
        )
        unit_meta = rows[0] if rows else {}
    except Exception:
        unit_meta = {}

    id_lote       = (unit_meta.get("id_lote") or "").strip()
    reefer_serial = (unit_meta.get("reefer_serial") or "").strip()
    subfolder_name = f"{unit_number}_{reefer_serial}" if reefer_serial else unit_number
    folder_path = f"{EVIDENCIAS_DIR}/{id_lote}/{subfolder_name}" if id_lote else f"{EVIDENCIAS_DIR}/{subfolder_name}"

    try:
        real_folder_path = _upload_with_retry(_ensure_folder, folder_path)
    except Exception as e:
        logger.error(f"[OneDrive] No se pudo crear carpeta ZIP '{folder_path}': {e}")
        raise

    nombre = f"{unit_number}_evidencias.zip"
    path   = f"{real_folder_path}/{nombre}"
    try:
        result  = _upload_with_retry(upload_large_file, zip_bytes, path, "application/zip")
        web_url = result.get("webUrl", "")
        logger.info(f"[OneDrive] ZIP subido: {path}")
        return web_url
    except Exception as e:
        logger.error(f"[OneDrive] Error subiendo ZIP {path}: {e}")
        raise


def sync_zip_lote(id_lote: str, zip_bytes: bytes) -> str:
    """
    Sube el ZIP de backup de un lote completo (antes de ocultarlo) a:
      carrier-transicold/Reportes/Backups_Lotes/<id_lote>_backup_<fecha>.zip
    """
    fecha  = datetime.now(TZ).strftime("%Y-%m-%d_%H%M")
    nombre = f"{_sanitize_folder_name(id_lote)}_backup_{fecha}.zip"
    folder_path = f"{REPORTES_DIR}/Backups_Lotes"
    try:
        real_folder_path = _upload_with_retry(_ensure_folder, folder_path)
    except Exception as e:
        logger.error(f"[OneDrive] No se pudo crear carpeta de backups '{folder_path}': {e}")
        raise

    path = f"{real_folder_path}/{nombre}"
    try:
        result  = _upload_with_retry(upload_large_file, zip_bytes, path, "application/zip")
        web_url = result.get("webUrl", "")
        logger.info(f"[OneDrive] Backup de lote subido: {path}")
        return web_url
    except Exception as e:
        logger.error(f"[OneDrive] Error subiendo backup de lote {path}: {e}")
        raise


# ── Auditoría: carpetas de evidencias duplicadas ──────────────────────────────

def _listar_subcarpetas(folder_path: str) -> list[dict]:
    """
    Lista las carpetas hijas directas de folder_path en OneDrive.
    Devuelve [] si la carpeta no existe o no tiene hijos.
    Cada item: {"name": str, "id": str, "childCount": int, "webUrl": str}
    """
    headers = {"Authorization": f"Bearer {_get_token()}"}
    folder_path = folder_path.strip("/")
    url = f"{GRAPH_BASE}/me/drive/root:/{folder_path}:/children?$top=999"

    items = []
    while url:
        resp = requests.get(url, headers=headers, timeout=20)
        if resp.status_code == 404:
            return []  # la carpeta padre no existe aún
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("value", []):
            if "folder" in item:
                items.append({
                    "name": item["name"],
                    "id": item["id"],
                    "childCount": item["folder"].get("childCount", 0),
                    "webUrl": item.get("webUrl", ""),
                })
        url = data.get("@odata.nextLink")  # paginación si hay muchas carpetas
        headers = {"Authorization": f"Bearer {_get_token()}"}  # refrescar token por si tarda
    return items


def auditar_carpetas_duplicadas_lote(id_lote: str) -> dict:
    """
    Revisa Evidencias/<id_lote>/ y agrupa las subcarpetas por unit_number
    (la parte del nombre antes del primer '_' o ' ' o '-'), para detectar
    si una misma unidad terminó con más de una carpeta por el bug histórico
    de usar reefer_model (mutable) en vez de reefer_serial (inmutable).

    Esta función SOLO LEE — no mueve ni borra nada en OneDrive.

    Devuelve:
      {
        "id_lote": str,
        "total_carpetas": int,
        "duplicados": [
          {
            "unit_number": str,
            "carpetas": [{"name", "id", "childCount", "webUrl"}, ...]
          }, ...
        ],
        "sin_duplicar": int
      }
    """
    folder_path = f"{EVIDENCIAS_DIR}/{_sanitize_folder_name(id_lote)}"
    subcarpetas = _listar_subcarpetas(folder_path)

    grupos: dict[str, list] = {}
    for carpeta in subcarpetas:
        nombre = carpeta["name"]
        # La parte antes del primer separador es el unit_number candidato
        unit_number = re_split_unit_number(nombre)
        grupos.setdefault(unit_number, []).append(carpeta)

    duplicados = [
        {"unit_number": un, "carpetas": carpetas}
        for un, carpetas in grupos.items()
        if len(carpetas) > 1
    ]
    sin_duplicar = sum(1 for carpetas in grupos.values() if len(carpetas) == 1)

    return {
        "id_lote": id_lote,
        "total_carpetas": len(subcarpetas),
        "duplicados": duplicados,
        "sin_duplicar": sin_duplicar,
    }


def re_split_unit_number(nombre_carpeta: str) -> str:
    """
    Extrae el unit_number candidato del nombre de una carpeta de evidencias,
    soportando los dos patrones históricos:
      "UNIT123_RF98765"   (patrón nuevo, reefer_serial)
      "UNIT123 - X300"    (patrón viejo, reefer_model)
      "UNIT123"           (sin sufijo, cualquier patrón)
    """
    for sep in (" - ", "_"):
        if sep in nombre_carpeta:
            return nombre_carpeta.split(sep, 1)[0].strip()
    return nombre_carpeta.strip()


def auditar_todos_los_lotes() -> dict:
    """
    Recorre todos los id_lote distintos registrados en la BD y audita
    cada uno con auditar_carpetas_duplicadas_lote(). Solo lectura.

    Devuelve:
      {
        "lotes_revisados": int,
        "lotes_con_duplicados": int,
        "total_unidades_duplicadas": int,
        "detalle": [ resultado de auditar_carpetas_duplicadas_lote(...), ... ]
                   (solo se incluyen lotes que SÍ tienen duplicados)
      }
    """
    from db import execute_read
    filas = execute_read(
        "SELECT DISTINCT id_lote FROM unidades WHERE id_lote IS NOT NULL AND id_lote != ''"
    )
    lotes = [f["id_lote"] for f in filas]

    detalle = []
    total_unidades_duplicadas = 0
    for id_lote in lotes:
        try:
            resultado = auditar_carpetas_duplicadas_lote(id_lote)
        except Exception as e:
            logger.warning(f"[OneDrive][auditoria] No se pudo auditar lote '{id_lote}': {e}")
            continue
        if resultado["duplicados"]:
            detalle.append(resultado)
            total_unidades_duplicadas += len(resultado["duplicados"])

    return {
        "lotes_revisados": len(lotes),
        "lotes_con_duplicados": len(detalle),
        "total_unidades_duplicadas": total_unidades_duplicadas,
        "detalle": detalle,
    }


# ── Fusión de carpetas duplicadas ─────────────────────────────────────────────

def _listar_archivos(folder_id: str) -> list[dict]:
    """Lista los archivos (no carpetas) hijos directos de una carpeta por su ID."""
    headers = {"Authorization": f"Bearer {_get_token()}"}
    url = f"{GRAPH_BASE}/me/drive/items/{folder_id}/children?$top=999"
    archivos = []
    while url:
        resp = requests.get(url, headers=headers, timeout=20)
        resp.raise_for_status()
        data = resp.json()
        for item in data.get("value", []):
            if "file" in item:
                archivos.append({"id": item["id"], "name": item["name"]})
        url = data.get("@odata.nextLink")
        headers = {"Authorization": f"Bearer {_get_token()}"}
    return archivos


def _mover_archivo(file_id: str, destino_folder_id: str, nuevo_nombre: str = None) -> dict:
    """
    Mueve un archivo a otra carpeta usando el endpoint nativo de Graph API
    (PATCH con parentReference). No descarga/re-sube — es instantáneo y no
    consume memoria del servidor. Si nuevo_nombre se da, lo renombra a la vez.
    """
    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }
    url = f"{GRAPH_BASE}/me/drive/items/{file_id}"
    body = {"parentReference": {"id": destino_folder_id}}
    if nuevo_nombre:
        body["name"] = nuevo_nombre
    resp = requests.patch(url, headers=headers, json=body, timeout=20)
    resp.raise_for_status()
    return resp.json()


def _renombrar_item(item_id: str, nuevo_nombre: str) -> dict:
    """Renombra una carpeta o archivo por su ID."""
    headers = {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
    }
    url = f"{GRAPH_BASE}/me/drive/items/{item_id}"
    resp = requests.patch(url, headers=headers, json={"name": nuevo_nombre}, timeout=20)
    resp.raise_for_status()
    return resp.json()


def _borrar_item(item_id: str) -> None:
    """Elimina una carpeta o archivo por su ID (va a la papelera de OneDrive, no se pierde)."""
    headers = {"Authorization": f"Bearer {_get_token()}"}
    url = f"{GRAPH_BASE}/me/drive/items/{item_id}"
    resp = requests.delete(url, headers=headers, timeout=20)
    if resp.status_code not in (204, 404):
        resp.raise_for_status()


def fusionar_carpeta_duplicada(
    carpeta_origen_id: str,
    carpeta_destino_id: str,
    nombre_final_destino: str,
) -> dict:
    """
    Fusiona el contenido de carpeta_origen (la más pequeña/antigua, sin sufijo)
    dentro de carpeta_destino (la más grande, con sufijo), renombrando el
    destino al patrón nuevo unit_number_reefer_serial al final.

    Pasos, con seguridad ante colisión de nombres:
      1. Lista archivos de origen y destino.
      2. Por cada archivo en origen: si su nombre YA existe en destino,
         se mueve con sufijo "_dup1", "_dup2"... para no sobrescribir nada.
         Si no hay colisión, se mueve con su nombre original.
      3. Verifica que origen quedó vacío (childCount == 0) antes de borrar.
      4. Borra la carpeta origen (va a la papelera de OneDrive — recuperable).
      5. Renombra la carpeta destino al patrón nuevo.

    Devuelve un reporte detallado de qué se movió, qué tuvo colisión,
    y si se pudo borrar la carpeta origen al final.
    """
    archivos_origen  = _listar_archivos(carpeta_origen_id)
    archivos_destino = _listar_archivos(carpeta_destino_id)
    nombres_destino = {a["name"] for a in archivos_destino}

    movidos = []
    renombrados_por_colision = []
    errores = []

    for archivo in archivos_origen:
        nombre = archivo["name"]
        nombre_final = nombre
        if nombre in nombres_destino:
            base, ext = (nombre.rsplit(".", 1) + [""])[:2] if "." in nombre else (nombre, "")
            n = 1
            while nombre_final in nombres_destino:
                nombre_final = f"{base}_dup{n}.{ext}" if ext else f"{base}_dup{n}"
                n += 1
            renombrados_por_colision.append({"original": nombre, "renombrado": nombre_final})

        try:
            _upload_with_retry(_mover_archivo, archivo["id"], carpeta_destino_id, nombre_final)
            nombres_destino.add(nombre_final)
            movidos.append(nombre_final)
        except Exception as e:
            errores.append({"archivo": nombre, "error": str(e)})
            logger.error(f"[OneDrive][fusion] No se pudo mover '{nombre}': {e}")

    # Verificar que origen quedó vacío antes de borrar
    origen_vacio = len(_listar_archivos(carpeta_origen_id)) == 0
    borrado_origen = False
    if origen_vacio and not errores:
        try:
            _borrar_item(carpeta_origen_id)
            borrado_origen = True
        except Exception as e:
            logger.error(f"[OneDrive][fusion] No se pudo borrar carpeta origen vacía: {e}")

    renombrado_destino = False
    if borrado_origen:
        try:
            _renombrar_item(carpeta_destino_id, nombre_final_destino)
            renombrado_destino = True
        except Exception as e:
            logger.error(f"[OneDrive][fusion] No se pudo renombrar carpeta destino: {e}")

    return {
        "archivos_movidos": len(movidos),
        "nombres_movidos": movidos,
        "colisiones_renombradas": renombrados_por_colision,
        "errores": errores,
        "origen_quedo_vacio": origen_vacio,
        "origen_borrado": borrado_origen,
        "destino_renombrado": renombrado_destino,
        "nombre_final": nombre_final_destino if renombrado_destino else None,
    }


def enviar_correo(destinatarios: list[str], asunto: str, cuerpo_html: str,
                   adjunto_nombre: str = None, adjunto_bytes: bytes = None) -> dict:
    """
    Envía un correo usando el mismo buzón autenticado por Graph (Mail.Send)
    que ya se usa para OneDrive.

    IMPORTANTE — requiere configuración adicional que NO viene gratis con
    lo que ya está montado para OneDrive:
      1. En el App Registration de Azure (portal.azure.com), agregar el
         permiso delegado "Mail.Send" (API permissions → Add a permission
         → Microsoft Graph → Delegated → Mail.Send) y darle "Grant admin
         consent" si aplica.
      2. El MS_REFRESH_TOKEN actual fue emitido solo con el scope de
         OneDrive (Files.ReadWrite, User.Read) — un scope que el usuario
         nunca consintió no se puede "agregar" después. Hay que volver a
         hacer el flujo de OAuth (login interactivo una vez) para obtener
         un refresh token nuevo que sí incluya Mail.Send, y reemplazar
         MS_REFRESH_TOKEN en Clever Cloud con ese valor.

    Sin ese paso, esta función lanzará un error 403 de Graph — por eso
    quien la llama (enviar_reporte_semanal) lo captura y loggea en vez de
    tronar el proceso.
    """
    mensaje = {
        "message": {
            "subject": asunto,
            "body": {"contentType": "HTML", "content": cuerpo_html},
            "toRecipients": [{"emailAddress": {"address": d}} for d in destinatarios],
        },
        "saveToSentItems": "true",
    }

    if adjunto_bytes is not None and adjunto_nombre:
        import base64
        mensaje["message"]["attachments"] = [{
            "@odata.type": "#microsoft.graph.fileAttachment",
            "name": adjunto_nombre,
            "contentBytes": base64.b64encode(adjunto_bytes).decode("ascii"),
        }]

    resp = requests.post(
        f"{GRAPH_BASE}/me/sendMail",
        headers={"Authorization": f"Bearer {_get_token()}", "Content-Type": "application/json"},
        json=mensaje,
        timeout=30,
    )
    if resp.status_code not in (200, 202):
        raise Exception(f"Graph sendMail falló: {resp.status_code} {resp.text[:300]}")
    return {"enviado": True, "destinatarios": destinatarios}
