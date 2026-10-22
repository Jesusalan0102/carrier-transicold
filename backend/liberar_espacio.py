"""
Libera espacio en la base de datos para no llegar al límite de 5 GB de TiDB Cloud Starter.

Idea ("buffer"): las fotos y videos recientes viven en la DB unos días (EVIDENCIAS_DIAS_EN_DB, por defecto 7);
ya respaldados y VERIFICADOS en OneDrive, se les quita el contenido a la DB. La fila queda (con su
onedrive_item_id) y la app ya sabe servir esos archivos directo desde OneDrive.

Antes de quitar el contenido de CUALQUIER fila se comprueba, una por una:
  1. Que haya un respaldo de la base de datos bueno de las últimas 36 h (si no, no hace nada).
  2. Que el archivo exista en OneDrive con el MISMO tamaño y el MISMO hash SHA-1 que el de la DB.
     (Para fotos que aún no están enlazadas, lo busca por hash en la carpeta de su unidad.)
Si algo no coincide, esa fila NO se toca. Nunca sube, reemplaza ni borra nada en OneDrive.

Activación:
  - A mano:   POST /api/respaldo/liberar-espacio?aplicar=false  (simulación)  ->  aplicar=true
  - Cada noche, justo después del respaldo: variable de entorno LIBERAR_ESPACIO=1
Variables opcionales: EVIDENCIAS_DIAS_EN_DB (7), DB_UMBRAL_MB (3500: por encima de esto no se
deja días de buffer), PURGA_ACEPTAR_TAMANO (0: si OneDrive no entrega hash, no libera nada).
"""
import hashlib
import logging
import os
import time
from urllib.parse import quote

import requests

import evidencia_partes as ep
from db import execute_read, execute_write

logger = logging.getLogger(__name__)


def _env_int(nombre: str, defecto: int) -> int:
    try:
        return int(os.getenv(nombre, str(defecto)))
    except ValueError:
        return defecto


DIAS_EN_DB = _env_int("EVIDENCIAS_DIAS_EN_DB", 7)
UMBRAL_MB = _env_int("DB_UMBRAL_MB", 3500)
HORAS_MAX_RESPALDO = 36
PRESUPUESTO_SEG = 30 * 60
LOTE = 100
ACEPTAR_TAMANO = os.getenv("PURGA_ACEPTAR_TAMANO", "0") == "1"


# ── espacio ocupado ────────────────────────────────────────────────────────
def estado_espacio() -> dict:
    """Tamaño aproximado de la DB (information_schema; TiDB lo estima, puede ir con retraso)."""
    try:
        filas = execute_read(
            "SELECT table_name AS tabla, COALESCE(data_length,0)+COALESCE(index_length,0) AS bytes "
            "FROM information_schema.tables WHERE table_schema=DATABASE() ORDER BY bytes DESC") or []
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}
    total = sum(float(f["bytes"] or 0) for f in filas)
    return {"ok": True, "total_mb": round(total / 1048576, 1), "limite_gratis_mb": 5120, "umbral_mb": UMBRAL_MB,
            "usa_buffer_completo": total / 1048576 < UMBRAL_MB,
            "tablas_mas_grandes": [{"tabla": f["tabla"], "mb": round(float(f["bytes"] or 0) / 1048576, 1)} for f in filas[:6]]}


def respaldo_reciente(horas: int = HORAS_MAX_RESPALDO) -> bool:
    import salud_evidencias as sv
    est = sv.leer_estado("respaldo") or {}
    ts = est.get("ts_ok")
    return bool(ts) and (time.time() - float(ts)) < horas * 3600


# ── OneDrive (solo lectura) ────────────────────────────────────────────────
def _auth(od) -> dict:
    return {"Authorization": f"Bearer {od._get_token()}"}


def _item(j: dict) -> dict:
    h = ((j.get("file") or {}).get("hashes") or {})
    return {"id": j["id"], "name": j.get("name", ""), "size": int(j.get("size") or 0),
            "webUrl": j.get("webUrl", ""), "sha1": (h.get("sha1Hash") or "").lower() or None}


def _listar(od, carpeta: str) -> list:
    out, url = [], (f"{od.GRAPH_BASE}/me/drive/root:/{quote(carpeta, safe='/')}:/children"
                    f"?$top=200&$select=id,name,size,webUrl,folder,file")
    while url:
        r = requests.get(url, headers=_auth(od), timeout=30)
        r.raise_for_status()
        j = r.json()
        out += [_item(x) for x in j.get("value", []) if "folder" not in x]
        url = j.get("@odata.nextLink")
    return out


def _info_item(od, item_id: str):
    r = requests.get(f"{od.GRAPH_BASE}/me/drive/items/{item_id}?select=id,name,size,webUrl,file",
                     headers=_auth(od), timeout=20)
    if r.status_code == 404:
        return None
    r.raise_for_status()
    return _item(r.json())


# ── contenido en la DB ─────────────────────────────────────────────────────
def _tamano_y_sha1(fila: dict):
    """(bytes, sha1) del archivo guardado en la DB. Si está en partes lo lee por trozos."""
    h, n = hashlib.sha1(), 0
    if fila["bytes"]:
        r = execute_read("SELECT contenido FROM evidencias WHERE id=%s", (fila["id"],))
        datos = r[0]["contenido"] if r else None
        if not datos:
            return 0, None
        datos = bytes(datos)
        h.update(datos)
        n = len(datos)
    else:
        total = ep.tamano_total(fila["id"])
        if not total:
            return 0, None
        for pedazo in ep.iterar_rango(fila["id"], 0, total - 1):
            h.update(pedazo)
            n += len(pedazo)
        if n != total:
            return n, None
    return n, h.hexdigest()


def verificar(tam: int, sha1: str, item) -> tuple:
    """¿El item de OneDrive es idéntico al archivo de la DB? -> (bool, motivo)"""
    if not item:
        return False, "no está en OneDrive"
    if item["size"] != tam:
        return False, f"tamaño distinto (OneDrive {item['size']} vs DB {tam})"
    if item.get("sha1"):
        return (True, "ok") if item["sha1"] == sha1 else (False, "el hash SHA-1 no coincide")
    return (True, "ok (solo tamaño)") if ACEPTAR_TAMANO else (False, "OneDrive no entregó hash")


# ── consulta de candidatas ────────────────────────────────────────────────
def _candidatas(desde_id: int, dias: int, n: int) -> list:
    edad, params = "", [desde_id]
    if dias > 0:
        edad = "AND (e.created_at IS NULL OR e.created_at < NOW() - INTERVAL %s DAY) "
        params.append(dias)
    params.append(n)
    return execute_read(
        "SELECT e.id, e.unit_number, e.nombre_archivo, e.onedrive_item_id, COALESCE(LENGTH(e.contenido),0) AS bytes "
        "FROM evidencias e WHERE e.id > %s "
        "AND (e.contenido IS NOT NULL OR EXISTS (SELECT 1 FROM evidencia_partes p WHERE p.evidencia_id=e.id)) "
        f"{edad}ORDER BY e.id LIMIT %s", tuple(params)) or []


# ── proceso principal ──────────────────────────────────────────────────────
def liberar_espacio(aplicar: bool = False, dias_buffer: int | None = None, forzar: bool = False,
                    presupuesto_seg: float = PRESUPUESTO_SEG, desde_id: int = 0) -> dict:
    """Quita de la DB el contenido de las evidencias ya verificadas en OneDrive. Nunca lanza excepción.
    aplicar=False: simula (lee y verifica, pero no cambia nada). Repetir con `siguiente_id` hasta `completo`."""
    import onedrive_service as od
    t0 = time.monotonic()
    esp = estado_espacio()
    if dias_buffer is None:
        dias_buffer = DIAS_EN_DB if (not esp.get("ok") or esp.get("usa_buffer_completo")) else 0
    res = {"modo": "APLICADO" if aplicar else "SIMULACIÓN (no se cambió nada)", "dias_buffer": dias_buffer,
           "db_mb_antes": esp.get("total_mb"), "revisados": 0, "verificados": 0, "liberados": 0, "enlazados": 0,
           "mb_liberados": 0.0, "sin_copia_en_onedrive": 0, "errores": [], "completo": True, "siguiente_id": desde_id}
    if aplicar and not forzar and not respaldo_reciente():
        return {**res, "ok": False, "completo": False,
                "error": f"No hay respaldo bueno de la base de datos en las últimas {HORAS_MAX_RESPALDO} h. "
                         "Corre el respaldo primero (no se liberó nada)."}
    listados: dict = {}
    ultimo = desde_id
    try:
        while True:
            if (time.monotonic() - t0) > presupuesto_seg:
                res["completo"] = False
                break
            lote = _candidatas(ultimo, dias_buffer, LOTE)
            if not lote:
                break
            for f in lote:
                ultimo = f["id"]
                if (time.monotonic() - t0) > presupuesto_seg:
                    res["completo"] = False
                    break
                res["revisados"] += 1
                try:
                    tam, sha1 = _tamano_y_sha1(f)
                    if not tam or not sha1:
                        raise Exception("el contenido en la DB está vacío o incompleto")
                    if f["onedrive_item_id"]:
                        item = _info_item(od, f["onedrive_item_id"])
                    else:
                        u = str(f["unit_number"] or "").strip()
                        if not u:
                            raise Exception("sin número de unidad: no se sabe en qué carpeta buscar")
                        if u not in listados:
                            listados[u] = _listar(od, od.carpeta_evidencia_unidad(u))
                        item = next((i for i in listados[u] if i["size"] == tam and i["sha1"] == sha1), None)
                    ok, motivo = verificar(tam, sha1, item)
                    if not ok:
                        res["sin_copia_en_onedrive"] += 1
                        if len(res["errores"]) < 20:
                            res["errores"].append({"id": f["id"], "archivo": f.get("nombre_archivo"), "motivo": motivo})
                        continue
                    res["verificados"] += 1
                    res["mb_liberados"] = round(res["mb_liberados"] + tam / 1048576, 2)
                    if not aplicar:
                        continue
                    if not f["onedrive_item_id"]:
                        execute_write(
                            "UPDATE evidencias SET onedrive_item_id=%s, onedrive_url=%s WHERE id=%s "
                            "AND (onedrive_item_id IS NULL OR onedrive_item_id='')", (item["id"], item["webUrl"], f["id"]))
                        res["enlazados"] += 1
                    execute_write("UPDATE evidencias SET contenido=NULL WHERE id=%s AND onedrive_item_id=%s",
                                  (f["id"], item["id"]))
                    ep.borrar_partes([f["id"]])
                    res["liberados"] += 1
                except Exception as e:
                    logger.error(f"[liberar] id={f['id']}: {e}")
                    if len(res["errores"]) < 20:
                        res["errores"].append({"id": f["id"], "archivo": f.get("nombre_archivo"), "motivo": str(e)[:160]})
            else:
                continue
            break                                     # el for terminó por break (sin tiempo)
    except Exception as e:
        logger.error(f"[liberar] falló: {e}")
        res["completo"] = False
        res["errores"].append({"motivo": str(e)[:200]})
    res["siguiente_id"] = ultimo
    res["segundos"] = round(time.monotonic() - t0, 1)
    res["ok"] = res["completo"] and not any("id" not in e for e in res["errores"])
    if aplicar:
        res["nota"] = "TiDB tarda un rato (recolección de basura) en reflejar el espacio liberado en su panel."
    return res
