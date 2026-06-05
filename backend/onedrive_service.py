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
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

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


def _ensure_folder(folder_path: str) -> str:
    """
    Garantiza que la carpeta (y toda su jerarquía) exista en OneDrive.
    Si alguna carpeta del camino no existe, la crea con PATCH (upsert).
    Devuelve el driveItem id de la carpeta final.

    La Graph API NO crea carpetas intermedias al hacer PUT de un archivo:
    si la carpeta no existe, el upload falla con 404.
    Este helper lo resuelve recorriendo cada nivel del path.
    """
    token = _get_token()
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    parts = [p for p in folder_path.strip("/").split("/") if p]
    current_path = ""

    for part in parts:
        current_path = f"{current_path}/{part}" if current_path else part
        url = f"{GRAPH_BASE}/me/drive/root:/{current_path}"

        # Comprobar si ya existe
        check = requests.get(url, headers=headers, timeout=15)
        if check.status_code == 200:
            continue  # carpeta ya existe, seguir al siguiente nivel

        # No existe → crearla en el padre
        if current_path == part:
            # Nivel raíz: crear dentro de /root
            parent_url = f"{GRAPH_BASE}/me/drive/root/children"
        else:
            parent_path = "/".join(current_path.split("/")[:-1])
            parent_url = f"{GRAPH_BASE}/me/drive/root:/{parent_path}:/children"

        body = {
            "name": part,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "rename",
        }
        create_resp = requests.post(parent_url, headers=headers, json=body, timeout=15)
        if create_resp.status_code not in (200, 201):
            raise Exception(
                f"No se pudo crear carpeta '{current_path}': "
                f"{create_resp.status_code} {create_resp.text[:200]}"
            )
        logger.info(f"[OneDrive] Carpeta creada: {current_path}")

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


def sync_evidencia(unit_number: str, nombre_archivo: str, contenido: bytes, unit_meta: dict = None) -> str:
    """
    Sube una foto de evidencia a OneDrive.

    Estructura de carpetas:
      carrier-transicold/Evidencias/<id_lote>/<unit_number> - <reefer_model>/

    Si unit_meta es None, consulta la DB para obtener id_lote y reefer_model.
    Si la unidad no tiene esos datos, usa solo unit_number como nombre de carpeta.

    Crea la jerarquía de carpetas si no existe antes de subir el archivo.
    Incluye reintentos automáticos.
    """
    # ── 1. Obtener metadata de la unidad ──────────────────────────────────
    if unit_meta is None:
        try:
            from db import execute_read
            rows = execute_read(
                "SELECT id_lote, reefer_model FROM unidades WHERE unit_number=%s LIMIT 1",
                (unit_number,)
            )
            unit_meta = rows[0] if rows else {}
        except Exception as e:
            logger.warning(f"[OneDrive] No se pudo obtener metadata de unidad {unit_number}: {e}")
            unit_meta = {}

    id_lote     = (unit_meta.get("id_lote") or "").strip()
    reefer_model = (unit_meta.get("reefer_model") or "").strip()

    # ── 2. Construir ruta de carpeta ──────────────────────────────────────
    # Nombre de subcarpeta: "<unit_number> - <reefer_model>" o solo "<unit_number>"
    subfolder_name = f"{unit_number} - {reefer_model}" if reefer_model else unit_number

    if id_lote:
        folder_path = f"{EVIDENCIAS_DIR}/{id_lote}/{subfolder_name}"
    else:
        folder_path = f"{EVIDENCIAS_DIR}/{subfolder_name}"

    # ── 3. Garantizar que la carpeta existe en OneDrive ───────────────────
    try:
        _upload_with_retry(_ensure_folder, folder_path)
    except Exception as e:
        logger.error(f"[OneDrive] No se pudo crear carpeta '{folder_path}': {e}")
        raise

    # ── 4. Subir el archivo ───────────────────────────────────────────────
    ext = nombre_archivo.rsplit(".", 1)[-1].lower() if "." in nombre_archivo else "jpg"
    mime_map = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "png": "image/png",  "gif": "image/gif",
        "webp": "image/webp", "pdf": "application/pdf",
    }
    content_type = mime_map.get(ext, "application/octet-stream")
    file_path = f"{folder_path}/{nombre_archivo}"

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
            "SELECT id_lote, reefer_model FROM unidades WHERE unit_number=%s LIMIT 1",
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
    from datetime import datetime
    if not fecha:
        fecha = datetime.now().strftime("%Y-%m-%d")
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
      carrier-transicold/Evidencias/<id_lote>/<unit_number> - <reefer_model>/
    """
    try:
        from db import execute_read
        rows = execute_read(
            "SELECT id_lote, reefer_model FROM unidades WHERE unit_number=%s LIMIT 1",
            (unit_number,)
        )
        unit_meta = rows[0] if rows else {}
    except Exception:
        unit_meta = {}

    id_lote      = (unit_meta.get("id_lote") or "").strip()
    reefer_model = (unit_meta.get("reefer_model") or "").strip()
    subfolder_name = f"{unit_number} - {reefer_model}" if reefer_model else unit_number
    folder_path = f"{EVIDENCIAS_DIR}/{id_lote}/{subfolder_name}" if id_lote else f"{EVIDENCIAS_DIR}/{subfolder_name}"

    try:
        _upload_with_retry(_ensure_folder, folder_path)
    except Exception as e:
        logger.error(f"[OneDrive] No se pudo crear carpeta ZIP '{folder_path}': {e}")
        raise

    nombre = f"{unit_number}_evidencias.zip"
    path   = f"{folder_path}/{nombre}"
    try:
        result  = _upload_with_retry(upload_large_file, zip_bytes, path, "application/zip")
        web_url = result.get("webUrl", "")
        logger.info(f"[OneDrive] ZIP subido: {path}")
        return web_url
    except Exception as e:
        logger.error(f"[OneDrive] Error subiendo ZIP {path}: {e}")
        raise
