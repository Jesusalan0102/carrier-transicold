"""
onedrive_service.py
-------------------
Módulo central para sincronizar archivos con OneDrive via Microsoft Graph API.
Usado por evidencias_router.py y dashboard_router.py de Carrier Transicold.

Variables de entorno requeridas (.env / Render):
  MS_CLIENT_ID      → App Registration > Application (client) ID
  MS_CLIENT_SECRET  → App Registration > Certificates & secrets
  MS_TENANT_ID      → App Registration > Directory (tenant) ID
  MS_USER_EMAIL     → Correo del usuario OneDrive donde se guardan los archivos
                      Ej: admin@tuempresa.onmicrosoft.com
"""

import os
import io
import logging
import msal
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

# ── Estructura de carpetas en OneDrive ──────────────────────────────────────
# OneDrive/
#   carrier-transicold/
#     Evidencias/
#       <unit_number>/         ← fotos por unidad
#     Reportes/
#       YYYY-MM/               ← reporte maestro Excel por mes

BASE_FOLDER    = "carrier-transicold"
EVIDENCIAS_DIR = f"{BASE_FOLDER}/Evidencias"
REPORTES_DIR   = f"{BASE_FOLDER}/Reportes"

GRAPH_BASE = "https://graph.microsoft.com/v1.0"


# ────────────────────────────────────────────────────────────────────────────
# AUTENTICACIÓN — Client Credentials (sin login de usuario)
# ────────────────────────────────────────────────────────────────────────────
def _get_token() -> str:
    """Obtiene access token usando client credentials (app-only)."""
    client_id     = os.getenv("MS_CLIENT_ID")
    client_secret = os.getenv("MS_CLIENT_SECRET")
    tenant_id     = os.getenv("MS_TENANT_ID")

    if not all([client_id, client_secret, tenant_id]):
        raise EnvironmentError(
            "Faltan variables de entorno: MS_CLIENT_ID, MS_CLIENT_SECRET, MS_TENANT_ID"
        )

    authority = f"https://login.microsoftonline.com/{tenant_id}"
    app = msal.ConfidentialClientApplication(
        client_id,
        authority=authority,
        client_credential=client_secret,
    )
    result = app.acquire_token_for_client(
        scopes=["https://graph.microsoft.com/.default"]
    )
    if "access_token" not in result:
        raise Exception(f"Error obteniendo token: {result.get('error_description', result)}")
    return result["access_token"]


def _headers() -> dict:
    return {"Authorization": f"Bearer {_get_token()}"}


def _user_email() -> str:
    email = os.getenv("MS_USER_EMAIL")
    if not email:
        raise EnvironmentError("Falta variable de entorno: MS_USER_EMAIL")
    return email


# ────────────────────────────────────────────────────────────────────────────
# SUBIR ARCHIVO — PUT de hasta 4 MB (fotos/PDFs individuales)
# ────────────────────────────────────────────────────────────────────────────
def upload_bytes(
    content: bytes,
    onedrive_path: str,
    content_type: str = "application/octet-stream",
) -> dict:
    """
    Sube bytes a OneDrive.
    onedrive_path: ruta relativa desde la raíz del drive.
      Ej: "carrier-transicold/Evidencias/ECO-001/foto1.jpg"
    Retorna el objeto JSON de Graph API con la URL del archivo.
    """
    email = _user_email()
    url = f"{GRAPH_BASE}/users/{email}/drive/root:/{onedrive_path}:/content"
    resp = requests.put(
        url,
        headers={**_headers(), "Content-Type": content_type},
        data=content,
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()


def upload_large_file(
    content: bytes,
    onedrive_path: str,
    content_type: str = "application/octet-stream",
) -> dict:
    """
    Sube archivos grandes (>4 MB) usando Upload Session de Graph API.
    Ideal para el reporte Excel maestro si crece mucho.
    """
    email = _user_email()
    # 1. Crear sesión
    session_url = f"{GRAPH_BASE}/users/{email}/drive/root:/{onedrive_path}:/createUploadSession"
    session_resp = requests.post(
        session_url,
        headers={**_headers(), "Content-Type": "application/json"},
        json={"item": {"@microsoft.graph.conflictBehavior": "replace"}},
        timeout=30,
    )
    session_resp.raise_for_status()
    upload_url = session_resp.json()["uploadUrl"]

    # 2. Subir en chunks de 5 MB
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


# ────────────────────────────────────────────────────────────────────────────
# HELPERS ESPECÍFICOS DE CARRIER TRANSICOLD
# ────────────────────────────────────────────────────────────────────────────

def sync_evidencia(unit_number: str, nombre_archivo: str, contenido: bytes) -> str:
    """
    Sube UNA foto de evidencia a:
      carrier-transicold/Evidencias/<unit_number>/<nombre_archivo>
    Retorna la webUrl del archivo en OneDrive.
    """
    # Detectar tipo según extensión
    ext = nombre_archivo.rsplit(".", 1)[-1].lower() if "." in nombre_archivo else "jpg"
    mime_map = {
        "jpg": "image/jpeg", "jpeg": "image/jpeg",
        "png": "image/png",  "gif": "image/gif",
        "webp": "image/webp", "pdf": "application/pdf",
    }
    content_type = mime_map.get(ext, "application/octet-stream")

    path = f"{EVIDENCIAS_DIR}/{unit_number}/{nombre_archivo}"
    try:
        result = upload_bytes(contenido, path, content_type)
        web_url = result.get("webUrl", "")
        logger.info(f"[OneDrive] Evidencia subida: {path}")
        return web_url
    except Exception as e:
        logger.error(f"[OneDrive] Error subiendo evidencia {path}: {e}")
        raise


def sync_reporte_maestro(excel_bytes: bytes, fecha: str = None) -> str:
    """
    Sube el reporte Excel maestro a:
      carrier-transicold/Reportes/YYYY-MM/Carrier_Reporte_YYYY-MM-DD.xlsx
    Retorna la webUrl del archivo.
    fecha: string YYYY-MM-DD (default: hoy)
    """
    if not fecha:
        fecha = datetime.now().strftime("%Y-%m-%d")
    mes   = fecha[:7]   # YYYY-MM
    nombre = f"Carrier_Reporte_{fecha}.xlsx"
    path  = f"{REPORTES_DIR}/{mes}/{nombre}"
    mime  = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    try:
        # Usar upload_large_file por si el Excel es grande
        result = upload_large_file(excel_bytes, path, mime)
        web_url = result.get("webUrl", "")
        logger.info(f"[OneDrive] Reporte subido: {path}")
        return web_url
    except Exception as e:
        logger.error(f"[OneDrive] Error subiendo reporte {path}: {e}")
        raise


def sync_zip_evidencias(unit_number: str, zip_bytes: bytes) -> str:
    """
    Sube el ZIP completo de evidencias de una unidad a:
      carrier-transicold/Evidencias/<unit_number>/<unit_number>_evidencias.zip
    """
    nombre = f"{unit_number}_evidencias.zip"
    path   = f"{EVIDENCIAS_DIR}/{unit_number}/{nombre}"
    try:
        result = upload_large_file(zip_bytes, path, "application/zip")
        web_url = result.get("webUrl", "")
        logger.info(f"[OneDrive] ZIP subido: {path}")
        return web_url
    except Exception as e:
        logger.error(f"[OneDrive] Error subiendo ZIP {path}: {e}")
        raise
