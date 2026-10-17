"""
Respaldo de FOTOS y VIDEOS de evidencia que viven en la base de datos -> OneDrive.

Qué resuelve
  - Fotos: la app las guarda SIEMPRE como blob en la DB y las manda a OneDrive en segundo plano; si ese
    envío falla (token vencido, sin red) nadie se entera y la foto queda solo en la DB.
  - Videos: si OneDrive falla al subirlos quedan en la DB (en una fila o en trozos de `evidencia_partes`).

Cómo lo hace (sin carpetas ni archivos repetidos)
  - Usa la MISMA carpeta que la creación de evidencias: Evidencias/<lote>/<unidad>_<serie reefer>/
    (`carpeta_evidencia_unidad`, que solo crea la carpeta si no existe).
  - Lista lo que ya hay en esa carpeta y compara nombre + tamaño: si ya está igual, no sube nada.
    Si falta o cambió, lo sube con el MISMO nombre (OneDrive lo reemplaza, no lo duplica).
  - Nombres deterministas: foto = su nombre original; si dos fotos de la misma unidad se llaman igual,
    la segunda lleva `_E<id>` antes de la extensión; video = A<tarea>_E<id>_<nombre> (como hoy, pero con el id
    de la fila en vez de un código al azar, así reintentar nunca crea otro archivo).
  - Videos: tras confirmar el tamaño en OneDrive se enlaza la fila (onedrive_item_id / onedrive_url).
    Fotos: no se toca la fila.
  - NUNCA borra nada de la DB. Se puede correr las veces que sea: lo ya respaldado se omite.
"""
import logging
import os
import re
import tempfile
import time
from urllib.parse import quote

import requests

import evidencia_partes as ep
from db import execute_read, execute_write

logger = logging.getLogger(__name__)

PRESUPUESTO_SEG = 45 * 60          # tope por corrida; lo que falte se completa en la siguiente
SIMPLE_MAX = 4 * 1024 * 1024       # hasta aquí PUT simple; arriba, sesión de subida por trozos
CHUNK = 5 * 1024 * 1024            # múltiplo de 320 KiB (requisito de Graph)
_VIDEO_REGEX = "[.](mp4|mov|webm|m4v|3gp|avi|mkv)$"
_VIDEO_RE = re.compile(r"\.(mp4|mov|webm|m4v|3gp|avi|mkv)$", re.I)
_PROHIBIDOS = re.compile(r'[\\/:*?"<>|#%&{}~]')
MIME = {
    "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp",
    "heic": "image/heic", "heif": "image/heif", "pdf": "application/pdf",
    "mp4": "video/mp4", "mov": "video/quicktime", "webm": "video/webm", "m4v": "video/x-m4v",
    "3gp": "video/3gpp", "avi": "video/x-msvideo", "mkv": "video/x-matroska",
}


# ── nombres ───────────────────────────────────────────────────────────────
def _ext(nombre: str) -> str:
    return nombre.rsplit(".", 1)[-1].lower() if "." in (nombre or "") else ""


def _es_video(fila: dict) -> bool:
    return (fila.get("tipo") or "") == "video" or bool(_VIDEO_RE.search(fila.get("nombre_archivo") or ""))


def _limpio(nombre: str, eid) -> str:
    n = _PROHIBIDOS.sub("_", nombre or "").strip(". ")
    return n or f"evidencia_{eid}"


def nombre_video(fila: dict) -> str:
    base = re.sub(r"[^\w.\- ]", "_", fila.get("nombre_archivo") or "video.mp4")
    return f"A{fila.get('asignacion_id') or 0}_E{fila['id']}_{base}"


def nombre_foto(fila: dict, usados: set) -> str:
    """Nombre original; si ya lo tomó otra foto de la misma unidad, se le agrega _E<id> (siempre el mismo)."""
    n = _limpio(fila.get("nombre_archivo"), fila["id"])
    if n.lower() in usados:
        base, punto, ext = n.rpartition(".")
        n = f"{base}_E{fila['id']}.{ext}" if punto else f"{n}_E{fila['id']}"
    usados.add(n.lower())
    return n


# ── OneDrive ──────────────────────────────────────────────────────────────
def _auth(od) -> dict:
    return {"Authorization": f"Bearer {od._get_token()}"}


def _listar(od, carpeta: str) -> dict:
    """Archivos que ya están en la carpeta: {nombre_en_minúsculas: {id, size, webUrl}} (con paginación)."""
    out = {}
    url = (f"{od.GRAPH_BASE}/me/drive/root:/{quote(carpeta, safe='/')}:/children"
           f"?$top=200&$select=id,name,size,webUrl,folder")
    while url:
        r = requests.get(url, headers=_auth(od), timeout=30)
        r.raise_for_status()
        j = r.json()
        for it in j.get("value", []):
            if "folder" not in it:
                out[it["name"].lower()] = {"id": it["id"], "size": int(it.get("size") or 0), "webUrl": it.get("webUrl", "")}
        url = j.get("@odata.nextLink")
    return out


def _put_trozo(url: str, headers: dict, data: bytes, intentos: int = 3):
    for i in range(intentos):
        try:
            r = requests.put(url, headers=headers, data=data, timeout=120)
            if r.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"HTTP {r.status_code}")
            r.raise_for_status()
            return r
        except requests.RequestException:
            if i == intentos - 1:
                raise
            time.sleep(2 * (i + 1))


def _subir_por_trozos(od, ruta_local: str, onedrive_path: str, content_type: str) -> dict:
    """Sesión de subida leyendo del disco de a CHUNK: nunca el archivo completo en RAM. Reemplaza si ya existe."""
    total = os.path.getsize(ruta_local)
    s = requests.post(
        f"{od.GRAPH_BASE}/me/drive/root:/{quote(onedrive_path, safe='/')}:/createUploadSession",
        headers={**_auth(od), "Content-Type": "application/json"},
        json={"item": {"@microsoft.graph.conflictBehavior": "replace"}}, timeout=30)
    s.raise_for_status()
    url = s.json()["uploadUrl"]
    resultado = {}
    try:
        with open(ruta_local, "rb") as fh:
            inicio = 0
            while inicio < total:
                trozo = fh.read(CHUNK)
                fin = inicio + len(trozo) - 1
                r = _put_trozo(url, {"Content-Length": str(len(trozo)), "Content-Range": f"bytes {inicio}-{fin}/{total}",
                                     "Content-Type": content_type}, trozo)
                resultado = r.json() if r.content else resultado
                inicio = fin + 1
    except Exception:
        try:
            requests.delete(url, timeout=15)            # cierra la sesión a medias
        except Exception:
            pass
        raise
    return resultado


# ── lectura del contenido (sin cargar todo en RAM cuando está en trozos) ───
def _volcar_a_disco(fila: dict, destino: str) -> int:
    """Escribe el archivo de la DB en `destino`. Devuelve los bytes escritos."""
    n = 0
    with open(destino, "wb") as fh:
        if fila["bytes"]:                                   # blob en una sola fila
            r = execute_read("SELECT contenido FROM evidencias WHERE id=%s", (fila["id"],))
            datos = r[0]["contenido"] if r else None
            if not datos:
                raise Exception("la fila ya no tiene contenido en la DB")
            datos = bytes(datos)
            fh.write(datos)
            n = len(datos)
        else:                                               # archivo grande guardado en trozos
            total = ep.tamano_total(fila["id"])
            for pedazo in ep.iterar_rango(fila["id"], 0, total - 1):
                fh.write(pedazo)
                n += len(pedazo)
    return n


# ── consultas ─────────────────────────────────────────────────────────────
_PENDIENTE = ("(e.onedrive_item_id IS NULL OR e.onedrive_item_id='') AND "
              "(e.contenido IS NOT NULL OR EXISTS (SELECT 1 FROM evidencia_partes p WHERE p.evidencia_id=e.id))")


def _unidades(solo_videos: bool, unidad: str | None) -> list:
    sql = f"SELECT DISTINCT e.unit_number FROM evidencias e WHERE {_PENDIENTE} AND e.unit_number IS NOT NULL AND e.unit_number<>''"
    params: list = []
    if solo_videos:
        sql += " AND (e.tipo='video' OR LOWER(e.nombre_archivo) REGEXP %s)"
        params.append(_VIDEO_REGEX)
    if unidad:
        sql += " AND e.unit_number=%s"
        params.append(unidad)
    sql += " ORDER BY e.unit_number"
    return [str(f["unit_number"]) for f in (execute_read(sql, tuple(params)) or [])]


def _filas_unidad(unidad: str) -> list:
    return execute_read(
        "SELECT e.id, e.unit_number, e.nombre_archivo, e.asignacion_id, e.tipo, e.mime_type, "
        "COALESCE(LENGTH(e.contenido),0) AS bytes "
        f"FROM evidencias e WHERE e.unit_number=%s AND {_PENDIENTE} ORDER BY e.id", (unidad,)) or []


# ── respaldo ──────────────────────────────────────────────────────────────
def respaldar_evidencias(aplicar: bool = True, solo_videos: bool = False,
                         presupuesto_seg: float = PRESUPUESTO_SEG, unidad: str | None = None) -> dict:
    """Copia a OneDrive las fotos/videos que están en la DB y aún no están (igual) en su carpeta.
    aplicar=False = simulación (cuenta lo pendiente sin subir ni cambiar nada). Nunca lanza excepción."""
    import onedrive_service as od
    t0 = time.monotonic()
    res = {"modo": "APLICADO" if aplicar else "SIMULACIÓN (no se cambió nada)", "unidades": 0, "revisados": 0,
           "ya_respaldados": 0, "subidos": 0, "vinculados": 0, "por_subir": 0, "mb_por_subir": 0.0,
           "mb_subidos": 0.0, "errores": [], "completo": True}
    try:
        unidades = _unidades(solo_videos, unidad)
    except Exception as e:
        return {**res, "ok": False, "completo": False, "error": f"No se pudo consultar la DB: {str(e)[:200]}"}

    def sin_tiempo() -> bool:
        return aplicar and (time.monotonic() - t0) > presupuesto_seg

    for u in unidades:
        if sin_tiempo():
            res["completo"] = False
            break
        try:
            filas = _filas_unidad(u)
            if solo_videos:
                filas = [f for f in filas if _es_video(f)]
            if not filas:
                continue
            res["unidades"] += 1
            carpeta = od.carpeta_evidencia_unidad(u)          # misma carpeta que la creación; no duplica
            existentes = _listar(od, carpeta)
        except Exception as e:
            res["errores"].append({"unidad": u, "error": str(e)[:200]})
            continue
        usados: set = set()
        for f in filas:
            res["revisados"] += 1
            esperado = int(f["bytes"] or 0) or ep.tamano_total(f["id"])
            video = _es_video(f)
            nombre = nombre_video(f) if video else nombre_foto(f, usados)
            if not esperado:
                res["errores"].append({"id": f["id"], "archivo": f.get("nombre_archivo"), "error": "sin contenido en la DB"})
                continue
            ct = MIME.get(_ext(nombre), "application/octet-stream")
            item = existentes.get(nombre.lower())
            ruta_od = f"{carpeta}/{nombre}"
            tmp = None
            try:
                if not (item and item["size"] == esperado):
                    if not aplicar:
                        res["por_subir"] += 1
                        res["mb_por_subir"] = round(res["mb_por_subir"] + esperado / 1048576, 1)
                        continue
                    if sin_tiempo():
                        res["completo"] = False
                        break
                    tmp = tempfile.NamedTemporaryFile(prefix="evid_", delete=False)
                    tmp.close()
                    escritos = _volcar_a_disco(f, tmp.name)
                    if escritos != esperado:
                        raise Exception(f"el contenido leído ({escritos}) no coincide con el esperado ({esperado})")
                    if escritos <= SIMPLE_MAX:
                        with open(tmp.name, "rb") as fh:
                            sube = od._upload_with_retry(od.upload_bytes, fh.read(), ruta_od, ct)
                    else:
                        sube = od._upload_with_retry(_subir_por_trozos, od, tmp.name, ruta_od, ct)
                    item = {"id": sube.get("id", ""), "size": 0, "webUrl": sube.get("webUrl", "")}
                    if not item["id"] or od.tamano_item(item["id"]) != esperado:
                        raise Exception("el tamaño en OneDrive no coincide; se conserva en la DB")
                    item["size"] = esperado
                    existentes[nombre.lower()] = item
                    res["subidos"] += 1
                    res["mb_subidos"] = round(res["mb_subidos"] + esperado / 1048576, 1)
                else:
                    res["ya_respaldados"] += 1
                if video and aplicar and item.get("id"):
                    execute_write(
                        "UPDATE evidencias SET onedrive_item_id=%s, onedrive_url=%s, tipo='video', "
                        "mime_type=COALESCE(NULLIF(mime_type,''), %s) WHERE id=%s "
                        "AND (onedrive_item_id IS NULL OR onedrive_item_id='')",
                        (item["id"], item.get("webUrl", ""), ct if ct.startswith("video/") else "video/mp4", f["id"]))
                    res["vinculados"] += 1
            except Exception as e:
                logger.error(f"[respaldo-evidencias] id={f['id']} {nombre}: {e}")
                res["errores"].append({"id": f["id"], "archivo": f.get("nombre_archivo"), "error": str(e)[:200]})
            finally:
                if tmp:
                    try:
                        os.remove(tmp.name)
                    except OSError:
                        pass
    res["errores"] = res["errores"][:20]
    res["segundos"] = round(time.monotonic() - t0, 1)
    res["ok"] = not res["errores"] and res["completo"]
    return res
