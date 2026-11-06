from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.concurrency import run_in_threadpool
from starlette.background import BackgroundTask
from db import execute_read, execute_write
from auth import verify_token
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from zoneinfo import ZoneInfo
import io
import os
import re
import csv
import uuid
import zipfile
import asyncio
import logging
import tempfile
import threading
import time
import concurrent.futures

TZ = ZoneInfo("America/Tijuana")
logger = logging.getLogger(__name__)

# ── Importación opcional de OneDrive ────────────────────────────────────────
try:
    from onedrive_service import sync_zip_lote, download_item_bytes as _od_download_item_bytes
    from onedrive_service import iter_item_bytes as _od_iter_item_bytes
    ONEDRIVE_ENABLED = True
except ImportError:
    ONEDRIVE_ENABLED = False
    _od_download_item_bytes = None
    _od_iter_item_bytes = None

def _tamano_partes_evidencia(evidencia_id):
    """Tamaño total si el archivo se guardó en trozos (evidencia_partes); 0 si no aplica."""
    try:
        from evidencia_partes import tamano_total
        return tamano_total(evidencia_id)
    except Exception:
        return 0


def _iterar_partes_evidencia(evidencia_id, total):
    """Entrega el archivo en trozos de <=4 MB sin juntarlo completo en RAM."""
    from evidencia_partes import iterar_rango
    return iterar_rango(evidencia_id, 0, total - 1)


def _leer_partes_evidencia(evidencia_id):
    """Archivo grande que se guardó en trozos (evidencia_partes); None si no aplica."""
    try:
        from evidencia_partes import leer_partes
        return leer_partes(evidencia_id)
    except Exception:
        return None


router = APIRouter(prefix="/api/unidades", tags=["unidades"])

CAMPOS_SERIES = [
    "vin_number","reefer_serial","reefer_model",
    "evaporator_serial_mjs11","evaporator_model_1",
    "evaporator_serial_mjd22","evaporator_model_2",
    "engine_serial","compressor_serial","generator_serial","battery_charger_serial"
]

# Modelos de evaporador disponibles para el desplegable (front y validación)
MODELOS_EVAPORADOR = ["", "MJD 1100", "MJS 1100", "MJD 2200", "MJS 2200", "N/A"]

class UnidadCreate(BaseModel):
    unit_number: str
    id_lote: str
    vin_number: Optional[str] = ""
    reefer_serial: Optional[str] = ""
    reefer_model: Optional[str] = ""
    evaporator_serial_mjs11: Optional[str] = ""
    evaporator_model_1: Optional[str] = ""
    evaporator_serial_mjd22: Optional[str] = ""
    evaporator_model_2: Optional[str] = ""
    engine_serial: Optional[str] = ""
    compressor_serial: Optional[str] = ""
    generator_serial: Optional[str] = ""
    battery_charger_serial: Optional[str] = ""

class SeriesUpdate(BaseModel):
    unit_number: str
    vin_number: Optional[str] = ""
    reefer_serial: Optional[str] = ""
    reefer_model: Optional[str] = ""
    evaporator_serial_mjs11: Optional[str] = ""
    evaporator_model_1: Optional[str] = ""
    evaporator_serial_mjd22: Optional[str] = ""
    evaporator_model_2: Optional[str] = ""
    engine_serial: Optional[str] = ""
    compressor_serial: Optional[str] = ""
    generator_serial: Optional[str] = ""
    battery_charger_serial: Optional[str] = ""
    # Series que se leen por foto. Default None: un cliente viejo que no los envía NO los borra.
    controller_serial: Optional[str] = None
    display_serial: Optional[str] = None
    ctd_module_serial: Optional[str] = None

# ═══════════════════════════════════════════════════════════════════════════
# ── GESTIÓN DE LOTES — helper y endpoints (ANTES de /{unidad_id}) ──────────
# ═══════════════════════════════════════════════════════════════════════════

_CARACTERES_INVALIDOS_WINDOWS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def _nombre_seguro(valor, fallback: str = "SIN_DATO") -> str:
    """Convierte un valor arbitrario en un nombre de carpeta/archivo válido
    en Windows (y compatible con Mac/Linux): sin < > : " / \\ | ? *, sin
    espacios/puntos al final. Si queda vacío, usa el fallback."""
    texto = ("" if valor is None else str(valor)).strip()
    texto = _CARACTERES_INVALIDOS_WINDOWS.sub("_", texto)
    texto = texto.strip(" .")
    return texto or fallback


ZIP_TROZO_BYTES = 4 * 1024 * 1024          # tamaño de trozo al leer blobs grandes de la DB
_EXT_VIDEO = {"mp4", "mov", "webm", "m4v", "3gp", "avi", "mkv"}


def _leer_blob_por_trozos(cur, evidencia_id, total):
    """Devuelve el blob de una evidencia en trozos de ZIP_TROZO_BYTES (SUBSTRING),
    para no traer a RAM un video completo de golpe."""
    pos = 1                                  # SUBSTRING en MySQL es base 1
    while pos <= total:
        cur.execute(
            "SELECT SUBSTRING(contenido, %s, %s) AS t FROM evidencias WHERE id=%s",
            (pos, ZIP_TROZO_BYTES, evidencia_id),
        )
        fila = cur.fetchone()
        trozo = fila["t"] if fila else None
        if not trozo:
            raise RuntimeError(f"La evidencia {evidencia_id} cambió o se truncó mientras se exportaba")
        yield bytes(trozo)
        pos += len(trozo)


def _escribir_stream_en_zip(zf, ruta, trozos, almacenar):
    """Escribe un archivo en el ZIP recibiendo el contenido por trozos.
    almacenar=True guarda sin comprimir (video: ya viene comprimido, y comprimirlo
    solo gasta CPU)."""
    if almacenar:
        info = zipfile.ZipInfo(ruta, date_time=time.localtime()[:6])
        info.compress_type = zipfile.ZIP_STORED
        destino = zf.open(info, "w", force_zip64=True)
    else:
        destino = zf.open(ruta, "w", force_zip64=True)
    with destino:
        for t in trozos:
            destino.write(t)


def _bajar_onedrive_a_temporal(item_id):
    """Baja un item de OneDrive por trozos a un archivo temporal en DISCO y
    devuelve su ruta. Si falla, no deja el temporal huérfano."""
    tmp = tempfile.NamedTemporaryFile(prefix="evid_od_", delete=False)
    ruta = tmp.name
    try:
        for trozo in _od_iter_item_bytes(item_id):
            tmp.write(trozo)
        tmp.close()
        return ruta
    except Exception:
        tmp.close()
        try:
            os.remove(ruta)
        except OSError:
            pass
        raise


def _registrar_faltante(progreso, lote, m, motivo):
    """Anota (en el dict de progreso del trabajo) una evidencia que NO se pudo incluir en el ZIP."""
    if progreso is None:
        return
    progreso.setdefault("faltantes", []).append(
        [lote, m.get("unit_number") or "", m.get("id") or "", m.get("nombre_archivo") or "", motivo]
    )


def _escribir_faltantes_csv(zf, progreso):
    """Si hubo evidencias que no se pudieron incluir, deja FALTANTES.csv dentro del ZIP."""
    if progreso is None or not progreso.get("faltantes"):
        return
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["Lote", "Unidad", "ID_evidencia", "Archivo", "Motivo"])
    w.writerows(progreso["faltantes"])
    zf.writestr("FALTANTES.csv", "\ufeff" + buf.getvalue())


def _escribir_evidencia_en_zip(zf, cur, m, ruta_zip):
    """Escribe UNA evidencia en el ZIP leyéndola por trozos (nunca junta archivos grandes en RAM).
    Devuelve (True, '') si quedó incluida o (False, motivo) si no se pudo."""
    ext = ruta_zip.rsplit(".", 1)[-1].lower() if "." in ruta_zip else ""
    es_video = (m.get("tipo") == "video") or ext in _EXT_VIDEO
    comp = zipfile.ZIP_STORED if es_video else None
    bytes_db = m.get("bytes_db") or 0
    try:
        if m.get("en_db") and bytes_db > 0:
            if bytes_db <= ZIP_TROZO_BYTES:
                cur.execute("SELECT contenido FROM evidencias WHERE id=%s", (m["id"],))
                fila = cur.fetchone()
                datos = bytes(fila["contenido"]) if fila and fila["contenido"] else b""
                if not datos:
                    return False, "la fila ya no tiene contenido en la base de datos"
                zf.writestr(ruta_zip, datos, compress_type=comp)
            else:
                _escribir_stream_en_zip(zf, ruta_zip, _leer_blob_por_trozos(cur, m["id"], bytes_db), es_video)
            return True, ""
        tam_partes = _tamano_partes_evidencia(m["id"])
        if tam_partes:
            _escribir_stream_en_zip(zf, ruta_zip, _iterar_partes_evidencia(m["id"], tam_partes), es_video)
            return True, ""
        if m.get("onedrive_item_id"):
            if not (ONEDRIVE_ENABLED and _od_iter_item_bytes is not None):
                return False, "solo existe en OneDrive y OneDrive no está disponible"
            ruta_temp = _bajar_onedrive_a_temporal(m["onedrive_item_id"])
            try:
                zf.write(ruta_temp, ruta_zip, compress_type=comp)
            finally:
                try:
                    os.remove(ruta_temp)
                except OSError:
                    pass
            return True, ""
        return False, "la fila no tiene archivo en la base de datos ni en OneDrive"
    except Exception as e:
        return False, str(e)[:120]


def _generar_zip_backup_lote_disco(id_lote: str, progreso=None) -> str:
    """
    ZIP de BACKUP de un lote escrito en DISCO (no en memoria): CSV de series + evidencias
    (fotos y videos) + reportes del lote. Devuelve la RUTA del ZIP.

    Antes se juntaban TODAS las fotos del lote en un diccionario en RAM y luego se armaba el ZIP
    entero en un BytesIO: con lotes de 20+ unidades eso agotaba la memoria del servidor y lo
    reiniciaba. Ahora cada evidencia se lee y se escribe al ZIP de una en una.
    """
    import pymysql
    from db import get_db_connection

    conn = get_db_connection()
    if not conn:
        raise RuntimeError("No hay conexión con la base de datos")

    tmp = tempfile.NamedTemporaryFile(prefix="backup_lote_", suffix=".zip", delete=False)
    tmp_path = tmp.name
    tmp.close()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            cur.execute("SELECT * FROM unidades WHERE id_lote=%s ORDER BY unit_number", (id_lote,))
            unidades = cur.fetchall()
            if not unidades:
                raise RuntimeError(f"El lote '{id_lote}' no tiene unidades")

            # Mismo orden que "Descargar evidencias" y que usa el equipo para archivar:
            #   evidencias/<lote>/<VIN>/<actividad>/<NN_actividad_vin_tecnico_fecha_hora>.ext  (+ informacion.csv)
            # Si una unidad no tiene VIN capturado se usa su # económico; si dos unidades del lote
            # comparten VIN se desambigua con _1, _2…
            lote_safe = _nombre_seguro(id_lote, "SIN_LOTE")
            vin_por_unidad, vin_usados = {}, {}
            for u in unidades:
                vin_base = (u.get("vin_number") or "").strip() or u["unit_number"]
                vin_safe = _nombre_seguro(vin_base, u["unit_number"])
                if vin_safe in vin_usados:
                    vin_usados[vin_safe] += 1
                    vin_safe = f"{vin_safe}_{vin_usados[vin_safe]}"
                else:
                    vin_usados[vin_safe] = 0
                vin_por_unidad[u["unit_number"]] = vin_safe

            unit_numbers = list(vin_por_unidad.keys())
            ph = ",".join(["%s"] * len(unit_numbers))
            try:
                cur.execute(
                    f"""SELECT e.id, e.unit_number, e.nombre_archivo, e.tecnico, e.equipo,
                               e.asignacion_id, e.tipo, e.onedrive_item_id,
                               (e.contenido IS NOT NULL) AS en_db, LENGTH(e.contenido) AS bytes_db,
                               COALESCE(e.created_at, NOW()) AS fecha_hora,
                               a.actividad_id AS actividad
                        FROM evidencias e
                        LEFT JOIN asignaciones a ON a.id = e.asignacion_id
                        WHERE e.unit_number IN ({ph})
                        ORDER BY e.unit_number, actividad, e.id""",
                    tuple(unit_numbers)
                )
                meta = cur.fetchall()
            except Exception as e_meta:
                logger.warning(f"[backup_lote] Fallback sin columnas nuevas: {e_meta}")
                cur.execute(
                    f"""SELECT e.id, e.unit_number, e.nombre_archivo, e.tecnico,
                               NULL AS equipo, e.asignacion_id, 'foto' AS tipo,
                               NULL AS onedrive_item_id,
                               (e.contenido IS NOT NULL) AS en_db, LENGTH(e.contenido) AS bytes_db,
                               COALESCE(e.created_at, NOW()) AS fecha_hora,
                               a.actividad_id AS actividad
                        FROM evidencias e
                        LEFT JOIN asignaciones a ON a.id = e.asignacion_id
                        WHERE e.unit_number IN ({ph})
                        ORDER BY e.unit_number, actividad, e.id""",
                    tuple(unit_numbers)
                )
                meta = cur.fetchall()

            if progreso is not None:
                progreso["total"] = len(meta)
                progreso["hechos"] = 0

            with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as zf:
                # CSV con las series de las unidades
                columnas = list(unidades[0].keys())
                buf = io.StringIO()
                w = csv.writer(buf)
                w.writerow(columnas)
                for u in unidades:
                    w.writerow([("" if u.get(c) is None else str(u.get(c))) for c in columnas])
                zf.writestr(f"unidades_{_nombre_seguro(id_lote, 'lote')}.csv", "\ufeff" + buf.getvalue())

                # Carpeta de cada VIN aunque no tenga evidencias (misma estructura que la exportación)
                for vin_safe in vin_por_unidad.values():
                    zf.writestr(f"evidencias/{lote_safe}/{vin_safe}/", "")

                # Evidencias: una por una, directo del origen al ZIP
                rutas_usadas = set()
                contadores = {}      # (vin_safe, actividad_safe) -> consecutivo
                filas_csv = {}       # (vin_safe, actividad_safe) -> [filas]
                for m in meta:
                    if progreso is not None:
                        progreso["hechos"] = progreso.get("hechos", 0) + 1
                        progreso["mensaje"] = f"Unidad {m['unit_number']}"
                    vin_safe = vin_por_unidad.get(m["unit_number"])
                    if not vin_safe:
                        continue
                    actividad_original = m.get("actividad") or "Sin actividad"
                    actividad_safe = _nombre_seguro(actividad_original, "Sin_actividad")
                    tecnico_original = m.get("tecnico") or ""
                    tecnico_safe = _nombre_seguro(tecnico_original, "Sin_tecnico")

                    fh = m.get("fecha_hora")
                    try:
                        fecha = fh.strftime("%Y-%m-%d")
                        hora_archivo = fh.strftime("%H-%M-%S")
                        hora_csv = fh.strftime("%H:%M:%S")
                    except Exception:
                        fecha, hora_archivo, hora_csv = "sin-fecha", "sin-hora", ""

                    nombre_orig = m.get("nombre_archivo") or ""
                    ext = nombre_orig.rsplit(".", 1)[-1].lower() if "." in nombre_orig else (
                        "mp4" if m.get("tipo") == "video" else "jpg"
                    )
                    ext = _nombre_seguro(ext, "jpg")

                    clave = (vin_safe, actividad_safe)
                    idx = contadores.get(clave, 0) + 1
                    base = f"{idx:02d}_{actividad_safe}_{vin_safe}_{tecnico_safe}_{fecha}_{hora_archivo}"
                    carpeta = f"evidencias/{lote_safe}/{vin_safe}/{actividad_safe}"
                    ruta_zip, sufijo = f"{carpeta}/{base}.{ext}", 1
                    while ruta_zip in rutas_usadas:      # nunca sobrescribir
                        sufijo += 1
                        ruta_zip = f"{carpeta}/{base}_{sufijo}.{ext}"
                    rutas_usadas.add(ruta_zip)

                    ok, motivo = _escribir_evidencia_en_zip(zf, cur, m, ruta_zip)
                    if not ok:
                        logger.warning(f"[backup_lote] evidencia id={m['id']} no incluida: {motivo}")
                        _registrar_faltante(progreso, id_lote, m, motivo)
                        continue
                    contadores[clave] = idx
                    filas_csv.setdefault(clave, []).append([
                        id_lote, vin_safe, actividad_original, tecnico_original,
                        fecha, hora_csv, ruta_zip.rsplit("/", 1)[-1], m.get("equipo") or ""
                    ])

                # informacion.csv por carpeta de actividad (igual que "Descargar evidencias")
                for (vin_safe, actividad_safe), filas in filas_csv.items():
                    lineas = ["Lote,VIN,Actividad,Tecnico,Fecha,Hora,Archivo,Equipo"]
                    for f in filas:
                        lineas.append(",".join('"' + str(x).replace('"', '""') + '"' for x in f))
                    zf.writestr(f"evidencias/{lote_safe}/{vin_safe}/{actividad_safe}/informacion.csv",
                                "\n".join(lineas))

                # Reportes de trabajo/problemas capturados por líderes para este lote
                try:
                    cur.execute(
                        "SELECT unit_number, tipo, detalle, username_lider, fecha, created_at "
                        "FROM reportes_unidad WHERE id_lote=%s ORDER BY unit_number, created_at",
                        (id_lote,)
                    )
                    reportes = cur.fetchall()
                    if reportes:
                        columnas_r = list(reportes[0].keys())
                        buf_r = io.StringIO()
                        wr = csv.writer(buf_r)
                        wr.writerow(columnas_r)
                        for r in reportes:
                            wr.writerow([("" if r.get(c) is None else str(r.get(c))) for c in columnas_r])
                        zf.writestr(f"reportes_lote_{_nombre_seguro(id_lote, 'lote')}.csv", "\ufeff" + buf_r.getvalue())
                except Exception as e_rep:
                    logger.warning(f"[backup_lote] No se pudieron incluir los reportes del lote: {e_rep}")

                _escribir_faltantes_csv(zf, progreso)
        return tmp_path
    except Exception:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise
    finally:
        conn.close()


def _subir_zip_lote_desde_disco(id_lote: str, ruta_local: str) -> str:
    """Sube un ZIP de backup de lote a OneDrive leyéndolo del disco por trozos de 5 MB
    (sync_zip_lote exige los bytes completos en RAM). Misma carpeta y nombre que sync_zip_lote:
      carrier-transicold/Reportes/Backups_Lotes/<id_lote>_backup_<fecha>.zip
    Devuelve el webUrl."""
    import requests
    from urllib.parse import quote
    import onedrive_service as od

    fecha = datetime.now(TZ).strftime("%Y-%m-%d_%H%M")
    nombre = f"{od._sanitize_folder_name(id_lote)}_backup_{fecha}.zip"
    carpeta = od._upload_with_retry(od._ensure_folder, f"{od.REPORTES_DIR}/Backups_Lotes")
    ruta_od = f"{carpeta}/{nombre}"

    s = requests.post(
        f"{od.GRAPH_BASE}/me/drive/root:/{quote(ruta_od, safe='/')}:/createUploadSession",
        headers={"Authorization": f"Bearer {od._get_token()}", "Content-Type": "application/json"},
        json={"item": {"@microsoft.graph.conflictBehavior": "replace"}}, timeout=30)
    s.raise_for_status()
    url = s.json()["uploadUrl"]

    total = os.path.getsize(ruta_local)
    CHUNK = 5 * 1024 * 1024            # múltiplo de 320 KiB (requisito de Graph)
    resultado = {}
    with open(ruta_local, "rb") as fh:
        inicio = 0
        while inicio < total:
            trozo = fh.read(CHUNK)
            fin = inicio + len(trozo) - 1
            ultimo_error = None
            for intento in range(3):
                try:
                    r = requests.put(
                        url,
                        headers={"Content-Length": str(len(trozo)),
                                 "Content-Range": f"bytes {inicio}-{fin}/{total}"},
                        data=trozo, timeout=120)
                    if r.status_code in (429, 500, 502, 503, 504):
                        raise requests.HTTPError(f"HTTP {r.status_code}")
                    r.raise_for_status()
                    resultado = r.json() if r.content else resultado
                    ultimo_error = None
                    break
                except requests.RequestException as e:
                    ultimo_error = e
                    time.sleep(2 * (intento + 1))
            if ultimo_error is not None:
                raise ultimo_error
            inicio = fin + 1
    return resultado.get("webUrl", "")


# ═══════════════════════════════════════════════════════════════════════════
# ── DESCARGA DE EVIDENCIAS ORGANIZADA: LOTE → VIN → ACTIVIDAD → EVIDENCIAS ──
# ═══════════════════════════════════════════════════════════════════════════
# No sustituye ni modifica cómo se almacenan las evidencias (siguen viviendo
# en la tabla `evidencias`, ligadas a unit_number / asignacion_id / tecnico /
# equipo). Esta función solo las reorganiza al momento de exportarlas a un ZIP.

def _generar_zip_evidencias_por_lotes(id_lotes: list, progreso=None) -> str:
    """
    ZIP en DISCO (archivo temporal) con estructura LOTE/VIN/ACTIVIDAD/evidencia,
    más un informacion.csv por carpeta de actividad (Lote,VIN,Actividad,Tecnico,
    Fecha,Hora,Archivo,Equipo). Reglas:
      - Cada lote seleccionado queda en su propia carpeta raíz; nunca se
        mezclan VINs o evidencias entre lotes.
      - Cada VIN del lote tiene su carpeta, aunque no tenga evidencias.
      - Solo se crean carpetas de actividad que sí tengan al menos una
        evidencia.
      - Evidencias de distintos técnicos para la misma actividad quedan
        juntas dentro de esa carpeta (no se separan por técnico).
      - Nunca se sobrescribe un archivo: ante una colisión de nombre se
        agrega un sufijo numérico.
      - Si alguna evidencia no se pudo incluir (por ejemplo, un video que solo vive
        en OneDrive y OneDrive no está disponible), se anota en FALTANTES.csv.

    `progreso` (opcional) es un dict que se va actualizando con 'total', 'hechos',
    'mensaje' y 'faltantes' para que el endpoint de estado pueda mostrar avance.

    Se devuelve la RUTA del ZIP (no los bytes en memoria): con lotes grandes,
    tener todas las evidencias descargadas + el ZIP comprimido completos en
    RAM al mismo tiempo puede tumbar el proceso por falta de memoria.
    Escribiendo directo a disco, en cualquier momento solo se mantiene en RAM
    la evidencia que se está procesando.
    """
    import pymysql
    from db import get_db_connection

    conn = get_db_connection()
    if not conn:
        raise RuntimeError("No hay conexión con la base de datos")

    tmp = tempfile.NamedTemporaryFile(prefix="evid_lotes_", suffix=".zip", delete=False)
    tmp_path = tmp.name
    tmp.close()

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            if progreso is not None:
                progreso["hechos"] = 0
                try:
                    ph0 = ",".join(["%s"] * len(id_lotes))
                    cur.execute(
                        "SELECT COUNT(*) AS n FROM evidencias e "
                        "INNER JOIN unidades u ON u.unit_number = e.unit_number "
                        f"WHERE u.id_lote IN ({ph0})", tuple(id_lotes)
                    )
                    fila_n = cur.fetchone() or {}
                    progreso["total"] = int(fila_n.get("n") or 0)
                except Exception as e_cnt:
                    logger.warning(f"[evidencias_lotes] No se pudo contar el total: {e_cnt}")
                    progreso["total"] = 0

            with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as zf:
                rutas_usadas = set()

                for id_lote in id_lotes:
                    lote_safe = _nombre_seguro(id_lote, "SIN_LOTE")
                    if progreso is not None:
                        progreso["mensaje"] = f"Lote {id_lote}"

                    cur.execute(
                        "SELECT unit_number, vin_number FROM unidades WHERE id_lote=%s ORDER BY unit_number",
                        (id_lote,)
                    )
                    unidades = cur.fetchall()
                    if not unidades:
                        continue

                    # VIN de carpeta por unidad (si no hay VIN capturado, se usa el
                    # #económico para no perder la unidad de la exportación) y
                    # desambiguación si dos unidades del lote comparten VIN.
                    vin_por_unidad = {}
                    vin_usados = {}
                    for u in unidades:
                        vin_base = (u.get("vin_number") or "").strip() or u["unit_number"]
                        vin_safe = _nombre_seguro(vin_base, u["unit_number"])
                        if vin_safe in vin_usados:
                            vin_usados[vin_safe] += 1
                            vin_safe = f"{vin_safe}_{vin_usados[vin_safe]}"
                        else:
                            vin_usados[vin_safe] = 0
                        vin_por_unidad[u["unit_number"]] = vin_safe

                        # Carpeta del VIN aunque quede vacía (entrada de directorio en el ZIP)
                        ruta_vin = f"{lote_safe}/{vin_safe}/"
                        if ruta_vin not in rutas_usadas:
                            zf.writestr(ruta_vin, "")
                            rutas_usadas.add(ruta_vin)

                    unit_numbers = list(vin_por_unidad.keys())
                    ph = ",".join(["%s"] * len(unit_numbers))

                    # Metadatos de evidencias + actividad (con fallback si el
                    # deploy aún no tiene las columnas tipo/equipo/onedrive_*).
                    try:
                        cur.execute(
                            f"""SELECT e.id, e.unit_number, e.nombre_archivo, e.tecnico, e.equipo,
                                       e.asignacion_id, e.tipo, e.onedrive_item_id,
                                       (e.contenido IS NOT NULL) AS en_db,
                                       LENGTH(e.contenido) AS bytes_db,
                                       COALESCE(e.created_at, NOW()) AS fecha_hora,
                                       a.actividad_id AS actividad
                                FROM evidencias e
                                LEFT JOIN asignaciones a ON a.id = e.asignacion_id
                                WHERE e.unit_number IN ({ph})
                                ORDER BY e.unit_number, actividad, e.id""",
                            tuple(unit_numbers)
                        )
                        meta = cur.fetchall()
                    except Exception as e_meta:
                        logger.warning(f"[evidencias_lotes] Fallback sin columnas nuevas: {e_meta}")
                        cur.execute(
                            f"""SELECT e.id, e.unit_number, e.nombre_archivo, e.tecnico,
                                       NULL AS equipo, e.asignacion_id, 'foto' AS tipo,
                                       NULL AS onedrive_item_id,
                                       (e.contenido IS NOT NULL) AS en_db,
                                       LENGTH(e.contenido) AS bytes_db,
                                       COALESCE(e.created_at, NOW()) AS fecha_hora,
                                       a.actividad_id AS actividad
                                FROM evidencias e
                                LEFT JOIN asignaciones a ON a.id = e.asignacion_id
                                WHERE e.unit_number IN ({ph})
                                ORDER BY e.unit_number, actividad, e.id""",
                            tuple(unit_numbers)
                        )
                        meta = cur.fetchall()

                    if not meta:
                        continue

                    # NO se cargan los archivos aquí: antes se acumulaban en RAM TODOS los
                    # blobs/videos del lote a la vez y eso tumbaba el servidor (502/503 por
                    # falta de memoria). Ahora cada evidencia se lee y se escribe al ZIP de
                    # una en una, por trozos, y se descarta.

                    contadores = {}       # (vin_safe, actividad_safe) -> consecutivo
                    filas_csv = {}        # (vin_safe, actividad_safe) -> [filas]

                    for m in meta:
                        if progreso is not None:
                            progreso["hechos"] = progreso.get("hechos", 0) + 1

                        en_db = bool(m.get("en_db")) and (m.get("bytes_db") or 0) > 0
                        en_od = (not en_db) and bool(m.get("onedrive_item_id")) \
                            and ONEDRIVE_ENABLED and _od_iter_item_bytes is not None
                        # Archivo grande guardado en trozos (evidencia_partes): tercera fuente posible
                        tam_partes = 0 if (en_db or en_od) else _tamano_partes_evidencia(m["id"])
                        if not (en_db or en_od or tam_partes):
                            if m.get("onedrive_item_id"):
                                _registrar_faltante(progreso, id_lote, m, "solo existe en OneDrive y OneDrive no está disponible")
                            else:
                                _registrar_faltante(progreso, id_lote, m, "la fila no tiene archivo en la base de datos ni en OneDrive")
                            continue

                        vin_safe = vin_por_unidad.get(m["unit_number"])
                        if not vin_safe:
                            # Evidencia de una unidad que ya no pertenece a este lote: se ignora
                            # (evita mezclar evidencias entre lotes/unidades reasignadas).
                            continue

                        actividad_original = m.get("actividad") or "Sin actividad"
                        actividad_safe = _nombre_seguro(actividad_original, "Sin_actividad")
                        tecnico_original = m.get("tecnico") or ""
                        tecnico_safe = _nombre_seguro(tecnico_original, "Sin_tecnico")

                        fh = m.get("fecha_hora")
                        try:
                            fecha = fh.strftime("%Y-%m-%d")
                            hora_archivo = fh.strftime("%H-%M-%S")
                            hora_csv = fh.strftime("%H:%M:%S")
                        except Exception:
                            fecha, hora_archivo, hora_csv = "sin-fecha", "sin-hora", ""

                        nombre_orig = m.get("nombre_archivo") or ""
                        ext = nombre_orig.rsplit(".", 1)[-1].lower() if "." in nombre_orig else (
                            "mp4" if m.get("tipo") == "video" else "jpg"
                        )
                        ext = _nombre_seguro(ext, "jpg")

                        ruta_temp = None
                        if en_od:
                            try:
                                ruta_temp = _bajar_onedrive_a_temporal(m["onedrive_item_id"])
                            except Exception as e_od:
                                logger.error(f"[evidencias_lotes] No se pudo bajar de OneDrive id={m['id']}: {e_od}")
                                _registrar_faltante(progreso, id_lote, m, f"no se pudo bajar de OneDrive: {str(e_od)[:100]}")
                                continue    # sin archivo no hay consecutivo ni fila en el CSV

                        clave = (vin_safe, actividad_safe)
                        contadores[clave] = contadores.get(clave, 0) + 1
                        idx = contadores[clave]

                        base = f"{idx:02d}_{actividad_safe}_{vin_safe}_{tecnico_safe}_{fecha}_{hora_archivo}"
                        ruta = f"{lote_safe}/{vin_safe}/{actividad_safe}/{base}.{ext}"
                        # Nunca sobrescribir: si hay colisión (p.ej. dos evidencias
                        # del mismo técnico en el mismo segundo), se agrega sufijo.
                        sufijo = 1
                        ruta_final = ruta
                        while ruta_final in rutas_usadas:
                            sufijo += 1
                            ruta_final = f"{lote_safe}/{vin_safe}/{actividad_safe}/{base}_{sufijo}.{ext}"
                        rutas_usadas.add(ruta_final)

                        es_video = (m.get("tipo") == "video") or ext in _EXT_VIDEO
                        try:
                            if ruta_temp:                                  # video que vive en OneDrive
                                zf.write(ruta_temp, ruta_final,
                                         compress_type=zipfile.ZIP_STORED if es_video else None)
                            elif tam_partes:                               # archivo grande guardado en partes
                                _escribir_stream_en_zip(
                                    zf, ruta_final, _iterar_partes_evidencia(m["id"], tam_partes), es_video)
                            elif (m.get("bytes_db") or 0) <= ZIP_TROZO_BYTES:   # foto / video chico
                                cur.execute("SELECT contenido FROM evidencias WHERE id=%s", (m["id"],))
                                fila_c = cur.fetchone()
                                datos = bytes(fila_c["contenido"]) if fila_c and fila_c["contenido"] else b""
                                zf.writestr(ruta_final, datos,
                                            compress_type=zipfile.ZIP_STORED if es_video else None)
                            else:                                          # blob grande en la DB: por trozos
                                _escribir_stream_en_zip(
                                    zf, ruta_final,
                                    _leer_blob_por_trozos(cur, m["id"], m["bytes_db"]), es_video)
                        finally:
                            if ruta_temp:
                                try:
                                    os.remove(ruta_temp)
                                except OSError:
                                    pass

                        filas_csv.setdefault(clave, []).append([
                            id_lote, vin_safe, actividad_original, tecnico_original,
                            fecha, hora_csv, ruta_final.rsplit("/", 1)[-1], m.get("equipo") or ""
                        ])

                    # informacion.csv por carpeta de actividad (no reemplaza la
                    # info visual que ya trae cada fotografía, es adicional).
                    for (vin_safe, actividad_safe), filas in filas_csv.items():
                        lineas = ["Lote,VIN,Actividad,Tecnico,Fecha,Hora,Archivo,Equipo"]
                        for f in filas:
                            lineas.append(",".join('"' + str(x).replace('"', '""') + '"' for x in f))
                        ruta_csv = f"{lote_safe}/{vin_safe}/{actividad_safe}/informacion.csv"
                        zf.writestr(ruta_csv, "\n".join(lineas))

                _escribir_faltantes_csv(zf, progreso)

        return tmp_path
    except Exception:
        # Si algo falla a medio camino, no dejar el temporal huérfano en disco.
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        raise
    finally:
        conn.close()


# GET /api/unidades/lotes  — listar lotes con conteo y estado oculto
@router.get("/lotes")
def listar_lotes(current_user=Depends(verify_token)):
    return execute_read("""
        SELECT id_lote,
               COUNT(*) AS total_unidades,
               MAX(oculto) AS oculto
        FROM unidades
        GROUP BY id_lote
        ORDER BY oculto ASC, id_lote ASC
    """)


# GET /api/unidades/lote-por-unidad?unit_number=A&unit_number=B  (uno o varios)
# Mapeo rápido unidad -> lote. Sin restricción de rol (accesible a técnicos
# también): solo expone el id_lote, nada sensible. Se usa en "Mis tareas"
# para agrupar visualmente las unidades del técnico por lote.
@router.get("/lote-por-unidad")
def lote_por_unidad(
    unit_number: List[str] = Query(..., description="Uno o varios números de unidad"),
    current_user=Depends(verify_token)
):
    unidades = list(dict.fromkeys(u.strip() for u in unit_number if u and u.strip()))
    if not unidades:
        return {}
    placeholders = ",".join(["%s"] * len(unidades))
    filas = execute_read(
        f"SELECT unit_number, id_lote FROM unidades WHERE unit_number IN ({placeholders})",
        tuple(unidades)
    )
    return {f["unit_number"]: f["id_lote"] for f in (filas or [])}


# GET /api/unidades/lotes/backup?id_lote=XXX
# ZIP de backup del lote. Se genera en DISCO (no en memoria) y se envía desde disco.
@router.get("/lotes/backup")
async def descargar_backup_lote(
    id_lote: str = Query(..., description="ID del lote a respaldar"),
    current_user=Depends(verify_token)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    logger.info(f"[backup_lote] Solicitado backup para id_lote='{id_lote}'")

    existentes = execute_read("SELECT unit_number FROM unidades WHERE id_lote=%s", (id_lote,))
    if not existentes:
        todos = execute_read("SELECT DISTINCT id_lote FROM unidades")
        lotes_str = ", ".join(r["id_lote"] for r in todos) if todos else "(ninguno)"
        raise HTTPException(
            status_code=404,
            detail=f"Lote '{id_lote}' no encontrado. Disponibles: {lotes_str}"
        )

    try:
        zip_path = await run_in_threadpool(_generar_zip_backup_lote_disco, id_lote)
    except Exception as e:
        logger.exception(f"[backup_lote] Falló la generación del ZIP para '{id_lote}': {e}")
        raise HTTPException(status_code=500, detail=f"Error al generar el ZIP: {e}")
    if not zip_path or not os.path.exists(zip_path) or os.path.getsize(zip_path) == 0:
        raise HTTPException(status_code=500, detail="Error al generar el ZIP")

    def _borrar_temp():
        try:
            os.remove(zip_path)
        except OSError:
            pass

    nombre_safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in id_lote)
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"backup_lote_{nombre_safe}.zip",
        headers={"Cache-Control": "no-store"},
        background=BackgroundTask(_borrar_temp)
    )


# GET /api/unidades/lotes/evidencias-zip?id_lote=A&id_lote=B  (uno o varios)
# ZIP organizado LOTE/VIN/ACTIVIDAD/evidencia + informacion.csv por actividad.
# (Versión directa, se conserva por compatibilidad. El botón de la app usa ahora los
#  endpoints de "zip-trabajo" de más abajo, que no se cancelan en lotes grandes.)
@router.get("/lotes/evidencias-zip")
async def descargar_evidencias_lotes(
    id_lote: List[str] = Query(..., description="Uno o más IDs de lote a exportar"),
    current_user=Depends(verify_token)
):
    if current_user["role"] not in ("admin", "visor"):
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores y visores")

    id_lotes = list(dict.fromkeys(l.strip() for l in id_lote if l and l.strip()))  # sin duplicados, conserva orden
    if not id_lotes:
        raise HTTPException(status_code=400, detail="Debes seleccionar al menos un lote")

    placeholders = ",".join(["%s"] * len(id_lotes))
    filas = execute_read(
        f"SELECT DISTINCT id_lote FROM unidades WHERE id_lote IN ({placeholders})",
        tuple(id_lotes)
    )
    existentes = {r["id_lote"] for r in (filas or [])}
    faltantes = [l for l in id_lotes if l not in existentes]
    if faltantes:
        raise HTTPException(status_code=404, detail=f"Lote(s) no encontrado(s): {', '.join(faltantes)}")

    logger.info(f"[evidencias_lotes] Exportación solicitada por {current_user.get('username')} para: {id_lotes}")
    try:
        zip_path = await run_in_threadpool(_generar_zip_evidencias_por_lotes, id_lotes)
    except Exception as e:
        logger.exception(f"[evidencias_lotes] Falló la generación del ZIP para {id_lotes}: {e}")
        raise HTTPException(status_code=500, detail=f"Error generando el ZIP de evidencias: {e}")
    if not zip_path or not os.path.exists(zip_path) or os.path.getsize(zip_path) == 0:
        if zip_path and os.path.exists(zip_path):
            os.remove(zip_path)
        raise HTTPException(status_code=500, detail="No se pudo generar el ZIP (sin datos para los lotes seleccionados)")

    peso_mb = os.path.getsize(zip_path) / (1024 * 1024)
    logger.info(f"[evidencias_lotes] ZIP generado para {id_lotes}: {peso_mb:.1f} MB")

    nombre_lotes = "_".join(_nombre_seguro(l, "LOTE") for l in id_lotes)
    if len(nombre_lotes) > 120:
        nombre_lotes = f"{len(id_lotes)}_lotes"

    def _borrar_temp():
        try:
            os.remove(zip_path)
        except OSError:
            pass

    # FileResponse transmite el archivo desde disco por partes (no lo vuelve
    # a cargar entero en RAM), y borra el temporal en cuanto termina de
    # enviarse, sin importar si el cliente cortó la descarga a medias.
    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=f"EVIDENCIAS_{nombre_lotes}.zip",
        headers={"Cache-Control": "no-store"},
        background=BackgroundTask(_borrar_temp)
    )


# ═══════════════════════════════════════════════════════════════════════════
# ── TRABAJOS DE ZIP EN SEGUNDO PLANO (evidencias de lotes y backup de lote) ─
# ═══════════════════════════════════════════════════════════════════════════
# Armar el ZIP de un lote grande (20+ unidades, fotos y videos) tarda minutos. Si se hace
# dentro de UNA sola petición HTTP, el navegador / el gateway cortan la conexión por falta
# de respuesta y la descarga "se cancela". Aquí el ZIP se genera en un hilo aparte:
#   1) POST  /lotes/zip-trabajo/iniciar        -> arranca el trabajo y devuelve job_id (al instante)
#   2) GET   /lotes/zip-trabajo/{job_id}       -> estado y progreso (la pantalla lo consulta cada 2 s)
#   3) GET   /lotes/zip-trabajo/{job_id}/archivo -> descarga el ZIP ya terminado (rápido, desde disco)
# Solo corre UN trabajo a la vez (el servidor es chico y trabaja con 1 worker).
# Los trabajos viven en memoria: si el servidor se reinicia, se pierden y hay que repetirlos.
_JOBS_ZIP = {}
_JOBS_ZIP_LOCK = threading.Lock()
_JOB_TTL_SEG = 90 * 60          # un ZIP terminado se conserva 90 min para poder descargarlo


def _borrar_archivo_trabajo(job):
    ruta = job.get("ruta")
    if ruta:
        try:
            os.remove(ruta)
        except OSError:
            pass


def _limpiar_trabajos_zip(usuario=None):
    """Quita trabajos viejos (y sus ZIP en disco). Si se indica usuario, también sus trabajos
    anteriores ya terminados, para no acumular archivos grandes en el disco del servidor."""
    ahora = time.time()
    for jid in list(_JOBS_ZIP.keys()):
        j = _JOBS_ZIP.get(jid)
        if not j or j["estado"] not in ("listo", "error"):
            continue
        vencido = (ahora - j["creado"]) > _JOB_TTL_SEG
        del_usuario = usuario is not None and j.get("usuario") == usuario
        if vencido or del_usuario:
            _borrar_archivo_trabajo(j)
            _JOBS_ZIP.pop(jid, None)


def _correr_trabajo_zip(job_id):
    job = _JOBS_ZIP.get(job_id)
    if not job:
        return
    try:
        job["estado"] = "generando"
        if job["tipo"] == "backup":
            ruta = _generar_zip_backup_lote_disco(job["lotes"][0], job)
        else:
            ruta = _generar_zip_evidencias_por_lotes(job["lotes"], job)
        if not ruta or not os.path.exists(ruta) or os.path.getsize(ruta) == 0:
            raise RuntimeError("No se generó el ZIP (sin datos para los lotes seleccionados)")
        job["ruta"] = ruta
        job["mb"] = round(os.path.getsize(ruta) / (1024 * 1024), 1)
        job["estado"] = "listo"
        logger.info(f"[zip_trabajo] {job_id} listo: {job['tipo']} {job['lotes']} → {job['mb']} MB, "
                    f"faltantes={len(job.get('faltantes') or [])}")
    except Exception as e:
        logger.exception(f"[zip_trabajo] {job_id} falló: {e}")
        job["estado"] = "error"
        job["error"] = str(e)[:300]


# POST /api/unidades/lotes/zip-trabajo/iniciar?tipo=evidencias|backup&id_lote=A&id_lote=B
@router.post("/lotes/zip-trabajo/iniciar")
def iniciar_trabajo_zip(
    tipo: str = Query("evidencias", description="evidencias (uno o varios lotes) o backup (un lote)"),
    id_lote: List[str] = Query(..., description="Uno o más IDs de lote"),
    current_user=Depends(verify_token)
):
    if tipo not in ("evidencias", "backup"):
        raise HTTPException(status_code=400, detail="tipo debe ser 'evidencias' o 'backup'")
    roles = ("admin", "visor") if tipo == "evidencias" else ("admin",)
    if current_user["role"] not in roles:
        raise HTTPException(status_code=403, detail="No tienes permiso para esta descarga")

    id_lotes = list(dict.fromkeys(l.strip() for l in id_lote if l and l.strip()))
    if not id_lotes:
        raise HTTPException(status_code=400, detail="Debes seleccionar al menos un lote")
    if tipo == "backup" and len(id_lotes) != 1:
        raise HTTPException(status_code=400, detail="El backup se genera de un lote a la vez")

    placeholders = ",".join(["%s"] * len(id_lotes))
    filas = execute_read(
        f"SELECT DISTINCT id_lote FROM unidades WHERE id_lote IN ({placeholders})", tuple(id_lotes)
    )
    existentes = {r["id_lote"] for r in (filas or [])}
    faltantes = [l for l in id_lotes if l not in existentes]
    if faltantes:
        raise HTTPException(status_code=404, detail=f"Lote(s) no encontrado(s): {', '.join(faltantes)}")

    usuario = current_user.get("username")
    with _JOBS_ZIP_LOCK:
        _limpiar_trabajos_zip()
        en_curso = [j for j in _JOBS_ZIP.values() if j["estado"] in ("en_cola", "generando")]
        for j in en_curso:
            if j["usuario"] == usuario and j["tipo"] == tipo and j["lotes"] == id_lotes:
                return {"job_id": j["id"], "reanudado": True}      # misma exportación: se reengancha
        if en_curso:
            quien = en_curso[0].get("usuario") or "otro usuario"
            raise HTTPException(
                status_code=409,
                detail=f"Ya hay una exportación en curso (iniciada por {quien}). Espera a que termine e inténtalo de nuevo."
            )
        _limpiar_trabajos_zip(usuario=usuario)                      # libera los ZIP anteriores de este usuario

        job_id = uuid.uuid4().hex[:12]
        nombre_lotes = "_".join(_nombre_seguro(l, "LOTE") for l in id_lotes)
        if len(nombre_lotes) > 120:
            nombre_lotes = f"{len(id_lotes)}_lotes"
        nombre_archivo = (f"backup_lote_{nombre_lotes}.zip" if tipo == "backup"
                          else f"EVIDENCIAS_{nombre_lotes}.zip")
        _JOBS_ZIP[job_id] = {
            "id": job_id, "tipo": tipo, "lotes": id_lotes, "usuario": usuario,
            "estado": "en_cola", "creado": time.time(), "nombre": nombre_archivo,
            "hechos": 0, "total": 0, "mensaje": "", "faltantes": [],
            "ruta": None, "mb": 0, "error": None,
        }
    logger.info(f"[zip_trabajo] {job_id} iniciado por {usuario}: {tipo} {id_lotes}")
    threading.Thread(target=_correr_trabajo_zip, args=(job_id,), daemon=True).start()
    return {"job_id": job_id, "reanudado": False}


def _trabajo_o_404(job_id: str, current_user):
    job = _JOBS_ZIP.get(job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail="Exportación no encontrada (el servidor pudo haberse reiniciado). Vuelve a iniciarla."
        )
    roles = ("admin", "visor") if job["tipo"] == "evidencias" else ("admin",)
    if current_user["role"] not in roles:
        raise HTTPException(status_code=403, detail="No tienes permiso para esta descarga")
    return job


# GET /api/unidades/lotes/zip-trabajo/{job_id}
@router.get("/lotes/zip-trabajo/{job_id}")
def estado_trabajo_zip(job_id: str, current_user=Depends(verify_token)):
    job = _trabajo_o_404(job_id, current_user)
    return {
        "estado": job["estado"], "hechos": job.get("hechos", 0), "total": job.get("total", 0),
        "mensaje": job.get("mensaje", ""), "error": job.get("error"), "mb": job.get("mb", 0),
        "faltantes": len(job.get("faltantes") or []), "nombre": job["nombre"],
    }


# GET /api/unidades/lotes/zip-trabajo/{job_id}/archivo
@router.get("/lotes/zip-trabajo/{job_id}/archivo")
def descargar_trabajo_zip(job_id: str, current_user=Depends(verify_token)):
    job = _trabajo_o_404(job_id, current_user)
    if job["estado"] != "listo":
        raise HTTPException(status_code=409, detail="El ZIP todavía no está listo")
    ruta = job.get("ruta")
    if not ruta or not os.path.exists(ruta):
        raise HTTPException(status_code=410, detail="El archivo ya no está en el servidor. Vuelve a generarlo.")
    # No se borra al terminar de enviarse: si la descarga se corta se puede repetir sin regenerar
    # (se limpia solo a los 90 min o al iniciar otra exportación del mismo usuario).
    return FileResponse(
        ruta, media_type="application/zip", filename=job["nombre"],
        headers={"Cache-Control": "no-store"},
    )


# POST /api/unidades/lotes/ocultar?id_lote=XXX&backup_onedrive=true/false
@router.post("/lotes/ocultar")
async def ocultar_lote(
    background_tasks: BackgroundTasks,
    id_lote: str = Query(...),
    backup_onedrive: bool = Query(False),
    current_user=Depends(verify_token)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")

    existentes = execute_read("SELECT id FROM unidades WHERE id_lote=%s", (id_lote,))
    if not existentes:
        raise HTTPException(status_code=404, detail=f"Lote '{id_lote}' no encontrado")

    # Ocultar el lote INMEDIATAMENTE — no esperar el backup
    execute_write("UPDATE unidades SET oculto=1 WHERE id_lote=%s", (id_lote,))

    respuesta = {
        "mensaje": f"Lote '{id_lote}' ocultado del dashboard",
        "unidades_afectadas": len(existentes),
    }

    if backup_onedrive:
        if not ONEDRIVE_ENABLED:
            respuesta["backup_aviso"] = "OneDrive no disponible en este servidor; el lote fue ocultado sin backup."
        else:
            # Lanzar backup en background — el cliente ya recibió confirmación.
            # El ZIP se arma en disco y se sube por trozos (sin juntar todo en RAM).
            def _tarea_backup():
                ruta = None
                try:
                    logger.info(f"[ocultar_lote] Iniciando backup background para '{id_lote}'")
                    ruta = _generar_zip_backup_lote_disco(id_lote)
                    web_url = _subir_zip_lote_desde_disco(id_lote, ruta)
                    logger.info(f"[ocultar_lote] Backup OneDrive completado: {web_url}")
                except Exception as e:
                    logger.error(f"[ocultar_lote] Backup OneDrive falló para '{id_lote}': {e}")
                finally:
                    if ruta:
                        try:
                            os.remove(ruta)
                        except OSError:
                            pass

            background_tasks.add_task(_tarea_backup)
            respuesta["backup_aviso"] = "El backup a OneDrive se está procesando en segundo plano."

    return respuesta


# POST /api/unidades/lotes/mostrar?id_lote=XXX
@router.post("/lotes/mostrar")
def mostrar_lote(
    id_lote: str = Query(...),
    current_user=Depends(verify_token)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    existentes = execute_read("SELECT id FROM unidades WHERE id_lote=%s", (id_lote,))
    if not existentes:
        raise HTTPException(status_code=404, detail=f"Lote '{id_lote}' no encontrado")
    execute_write("UPDATE unidades SET oculto=0 WHERE id_lote=%s", (id_lote,))
    return {
        "mensaje": f"Lote '{id_lote}' visible nuevamente en el dashboard",
        "unidades_afectadas": len(existentes),
    }


# GET /api/unidades/lotes/auditar-carpetas-duplicadas
# Solo lectura: revisa OneDrive y reporta carpetas de evidencias duplicadas
# por unidad (causadas por el bug histórico de reefer_model mutable).
# No mueve ni borra nada — es insumo para decidir la fusión manual.
@router.get("/lotes/auditar-carpetas-duplicadas")
async def auditar_carpetas_duplicadas(
    id_lote: Optional[str] = Query(None, description="Si se omite, audita todos los lotes"),
    current_user=Depends(verify_token)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")

    from onedrive_service import auditar_carpetas_duplicadas_lote, auditar_todos_los_lotes

    try:
        if id_lote:
            resultado = await run_in_threadpool(auditar_carpetas_duplicadas_lote, id_lote)
            resultado["lotes_revisados"] = 1
            resultado["lotes_con_duplicados"] = 1 if resultado["duplicados"] else 0
            resultado["total_unidades_duplicadas"] = len(resultado["duplicados"])
            resultado["detalle"] = [resultado] if resultado["duplicados"] else []
        else:
            resultado = await run_in_threadpool(auditar_todos_los_lotes)
    except Exception as e:
        logger.error(f"[auditoria] Error auditando carpetas: {e}")
        raise HTTPException(status_code=502, detail=f"No se pudo auditar OneDrive: {e}")

    return resultado


# POST /api/unidades/lotes/fusionar-carpeta-duplicada
# Fusiona DOS carpetas de evidencias detectadas como duplicadas para la
# misma unidad: mueve el contenido de la carpeta pequeña/vieja (sin sufijo)
# dentro de la carpeta grande/nueva, renombra el resultado al patrón
# unit_number_reefer_serial, y borra la carpeta vieja ya vacía.
#
# Requiere los IDs de OneDrive de ambas carpetas (vienen del endpoint de
# auditoría) — esto evita adivinar o volver a buscar por nombre, y previene
# fusionar la carpeta equivocada por error de tipeo.
@router.post("/lotes/fusionar-carpeta-duplicada")
async def fusionar_carpeta_duplicada_endpoint(
    unit_number: str = Query(...),
    carpeta_chica_id: str = Query(..., description="ID de OneDrive de la carpeta con MENOS archivos"),
    carpeta_grande_id: str = Query(..., description="ID de OneDrive de la carpeta con MÁS archivos"),
    current_user=Depends(verify_token)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")

    filas = execute_read(
        "SELECT reefer_serial FROM unidades WHERE unit_number=%s LIMIT 1", (unit_number,)
    )
    if not filas:
        raise HTTPException(status_code=404, detail=f"Unidad '{unit_number}' no encontrada en BD")

    reefer_serial = (filas[0].get("reefer_serial") or "").strip()
    nombre_final = f"{unit_number}_{reefer_serial}" if reefer_serial else unit_number

    from onedrive_service import fusionar_carpeta_duplicada

    try:
        resultado = await run_in_threadpool(
            fusionar_carpeta_duplicada, carpeta_chica_id, carpeta_grande_id, nombre_final
        )
    except Exception as e:
        logger.error(f"[fusion] Error fusionando carpetas de '{unit_number}': {e}")
        raise HTTPException(status_code=502, detail=f"No se pudo fusionar en OneDrive: {e}")

    resultado["unit_number"] = unit_number
    return resultado


# GET /api/unidades/ficha?q=XXX
# "Ficha 360°" de una unidad: busca q en CUALQUIER identificador de serie
# (unit_number, VIN, reefer_serial, motor, compresor, generador, etc.) y
# devuelve TODA la información relacionada: datos completos de la unidad,
# actividades/asignaciones con su técnico y estado, comentarios de cada
# actividad, toma de valores registrados, tickets abiertos/cerrados,
# conteo de evidencias, y estado de lote (oculto/visible + backup OneDrive
# si existe).
#
# Esta ruta debe declararse ANTES de /{unidad_id} para que FastAPI no la
# confunda con un path param.
CAMPOS_SERIE_BUSCABLES = [
    "unit_number", "id_lote", "vin_number", "reefer_serial", "reefer_model",
    "evaporator_serial_mjs11", "evaporator_serial_mjd22",
    "engine_serial", "compressor_serial", "generator_serial",
    "battery_charger_serial", "controller_serial", "display_serial", "ctd_module_serial",
]

@router.get("/ficha")
def ficha_unidad(q: str = Query(..., min_length=1), current_user=Depends(verify_token)):
    q = q.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Debes indicar un valor de búsqueda")

    # 1. Buscar la(s) unidad(es) por CUALQUIER campo de serie o el número de
    #    lote (coincidencia exacta primero; si no hay, se intenta parcial).
    #    Si el valor buscado corresponde a un lote con varias unidades,
    #    no se elige una al azar: se devuelve la lista completa para que
    #    el usuario seleccione cuál ficha quiere ver.
    condiciones = " OR ".join(f"{c}=%s" for c in CAMPOS_SERIE_BUSCABLES)
    params = [q] * len(CAMPOS_SERIE_BUSCABLES)
    filas = execute_read(
        f"SELECT * FROM unidades WHERE {condiciones} ORDER BY unit_number LIMIT 50",
        tuple(params)
    )

    if not filas:
        condiciones_like = " OR ".join(f"{c} LIKE %s" for c in CAMPOS_SERIE_BUSCABLES)
        params_like = [f"%{q}%"] * len(CAMPOS_SERIE_BUSCABLES)
        filas = execute_read(
            f"SELECT * FROM unidades WHERE {condiciones_like} ORDER BY unit_number LIMIT 50",
            tuple(params_like)
        )

    if not filas:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró ninguna unidad con '{q}' en VIN, series, lote o número económico"
        )

    if len(filas) > 1:
        return {
            "seleccion_multiple": True,
            "criterio": q,
            "unidades": [
                {
                    "unit_number": f["unit_number"],
                    "id_lote": f.get("id_lote"),
                    "vin_number": f.get("vin_number"),
                    "reefer_model": f.get("reefer_model"),
                }
                for f in filas
            ],
        }

    unidad = filas[0]
    unit_number = unidad["unit_number"]

    # 2. Asignaciones (actividades) de esta unidad — qué se ha hecho,
    #    quién lo hizo, en qué estado
    asignaciones = execute_read(
        "SELECT * FROM asignaciones WHERE unidad=%s ORDER BY id DESC", (unit_number,)
    )

    # 3. Comentarios de cada asignación de esta unidad
    asignacion_ids = [a["id"] for a in asignaciones]
    comentarios = []
    if asignacion_ids:
        placeholders = ",".join(["%s"] * len(asignacion_ids))
        comentarios = execute_read(
            f"SELECT * FROM comentarios_actividades WHERE asignacion_id IN ({placeholders}) "
            f"ORDER BY fecha DESC",
            tuple(asignacion_ids)
        )

    # 4. Toma de valores registrados en cualquiera de sus asignaciones
    toma_valores = []
    if asignacion_ids:
        placeholders = ",".join(["%s"] * len(asignacion_ids))
        toma_valores = execute_read(
            f"SELECT * FROM toma_valores_datos WHERE asignacion_id IN ({placeholders})",
            tuple(asignacion_ids)
        )

    # 5. Tickets de esta unidad
    tickets = execute_read(
        "SELECT * FROM tickets WHERE unit_number=%s ORDER BY id DESC", (unit_number,)
    )

    # 6. Evidencias — conteo total y lista de nombres (sin el contenido
    #    binario, para no inflar la respuesta)
    evidencias_count = execute_read(
        "SELECT COUNT(*) AS total FROM evidencias WHERE unit_number=%s", (unit_number,)
    )[0]["total"]
    evidencias_lista = execute_read(
        "SELECT id, nombre_archivo, tecnico, created_at FROM evidencias "
        "WHERE unit_number=%s ORDER BY created_at DESC LIMIT 200",
        (unit_number,)
    ) if evidencias_count else []

    # 7. Estado de lote: oculto/visible y si hay backup registrado en OneDrive
    lote_backup = None
    if unidad.get("id_lote"):
        rows_backup = execute_read(
            "SELECT * FROM lotes_backup_status WHERE id_lote=%s LIMIT 1",
            (unidad["id_lote"],)
        ) if _tabla_existe("lotes_backup_status") else []
        lote_backup = rows_backup[0] if rows_backup else None

    return {
        "unidad": unidad,
        "asignaciones": asignaciones,
        "comentarios": comentarios,
        "toma_valores": toma_valores,
        "tickets": tickets,
        "evidencias_total": evidencias_count,
        "evidencias": evidencias_lista,
        "lote_backup": lote_backup,
    }


# GET /api/unidades/timeline?q=XXX
# Línea de tiempo unificada de una unidad: PDI + asignaciones + tickets +
# evidencias, todo en un solo arreglo ordenado cronológicamente. Reutiliza
# la misma búsqueda por cualquier identificador de serie que /ficha.
@router.get("/timeline")
def timeline_unidad(q: str = Query(..., min_length=1), current_user=Depends(verify_token)):
    q = q.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Debes indicar un valor de búsqueda")

    condiciones = " OR ".join(f"{c}=%s" for c in CAMPOS_SERIE_BUSCABLES)
    params = [q] * len(CAMPOS_SERIE_BUSCABLES)
    filas = execute_read(
        f"SELECT * FROM unidades WHERE {condiciones} ORDER BY unit_number LIMIT 50",
        tuple(params)
    )
    if not filas:
        condiciones_like = " OR ".join(f"{c} LIKE %s" for c in CAMPOS_SERIE_BUSCABLES)
        params_like = [f"%{q}%"] * len(CAMPOS_SERIE_BUSCABLES)
        filas = execute_read(
            f"SELECT * FROM unidades WHERE {condiciones_like} ORDER BY unit_number LIMIT 50",
            tuple(params_like)
        )
    if not filas:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró ninguna unidad con '{q}' en VIN, series, lote o número económico"
        )
    if len(filas) > 1:
        return {
            "seleccion_multiple": True,
            "criterio": q,
            "unidades": [
                {"unit_number": f["unit_number"], "id_lote": f.get("id_lote"),
                 "vin_number": f.get("vin_number"), "reefer_model": f.get("reefer_model")}
                for f in filas
            ],
        }

    unidad = filas[0]
    unit_number = unidad["unit_number"]
    eventos = []

    # ── PDI: se crea una vez por unidad, marca el "nacimiento" del registro ──
    if _tabla_existe("pdi_inspecciones"):
        for p in execute_read(
            "SELECT tipo, estado, tecnico_inspecciono, created_at FROM pdi_inspecciones "
            "WHERE unit_number=%s ORDER BY created_at", (unit_number,)
        ):
            eventos.append({
                "fecha": p["created_at"],
                "tipo": "pdi",
                "titulo": f"PDI {p['tipo']} — {p['estado']}",
                "detalle": p.get("tecnico_inspecciono") or "",
            })

    # ── Asignaciones: cada actividad genera hasta 3 puntos en la línea de
    #    tiempo (asignada / iniciada / completada) cuando esa fecha existe ──
    asignaciones = execute_read(
        "SELECT actividad_id, tecnico, estado, fecha_asignacion, fecha_inicio, fecha_fin "
        "FROM asignaciones WHERE unidad=%s", (unit_number,)
    )
    for a in asignaciones:
        if a.get("fecha_asignacion"):
            eventos.append({
                "fecha": a["fecha_asignacion"], "tipo": "asignacion",
                "titulo": f"Actividad asignada: {a['actividad_id']}",
                "detalle": f"Técnico: {a['tecnico']}",
            })
        if a.get("fecha_inicio"):
            eventos.append({
                "fecha": a["fecha_inicio"], "tipo": "asignacion",
                "titulo": f"Actividad iniciada: {a['actividad_id']}",
                "detalle": f"Técnico: {a['tecnico']}",
            })
        if a.get("fecha_fin"):
            eventos.append({
                "fecha": a["fecha_fin"], "tipo": "asignacion",
                "titulo": f"Actividad completada: {a['actividad_id']}",
                "detalle": f"Técnico: {a['tecnico']}",
            })

    # ── Tickets: creación / atención / reporte de cierre ──────────────────
    for t in execute_read(
        "SELECT ticket_num, descripcion, creado_por, fecha_creacion, "
        "fecha_atencion, fecha_reporte, reporte_enviado "
        "FROM tickets WHERE unit_number=%s", (unit_number,)
    ):
        if t.get("fecha_creacion"):
            eventos.append({
                "fecha": t["fecha_creacion"], "tipo": "ticket",
                "titulo": f"Ticket #{t['ticket_num']} creado",
                "detalle": (t.get("descripcion") or "")[:140],
            })
        if t.get("fecha_atencion"):
            eventos.append({
                "fecha": t["fecha_atencion"], "tipo": "ticket",
                "titulo": f"Ticket #{t['ticket_num']} atendido",
                "detalle": "",
            })
        if t.get("fecha_reporte") and t.get("reporte_enviado"):
            eventos.append({
                "fecha": t["fecha_reporte"], "tipo": "ticket",
                "titulo": f"Ticket #{t['ticket_num']} cerrado con reporte",
                "detalle": "",
            })

    # ── Evidencias subidas ─────────────────────────────────────────────────
    for e in execute_read(
        "SELECT nombre_archivo, tecnico, created_at FROM evidencias "
        "WHERE unit_number=%s ORDER BY created_at", (unit_number,)
    ):
        if e.get("created_at"):
            eventos.append({
                "fecha": e["created_at"], "tipo": "evidencia",
                "titulo": f"Evidencia subida: {e['nombre_archivo']}",
                "detalle": f"Técnico: {e['tecnico']}" if e.get("tecnico") else "",
            })

    eventos = [ev for ev in eventos if ev["fecha"] is not None]
    eventos.sort(key=lambda ev: ev["fecha"])

    return {
        "unit_number": unit_number,
        "id_lote": unidad.get("id_lote"),
        "vin_number": unidad.get("vin_number"),
        "reefer_model": unidad.get("reefer_model"),
        "total_eventos": len(eventos),
        "eventos": eventos,
    }


def _tabla_existe(nombre_tabla: str) -> bool:
    """Verifica si una tabla existe en la BD, para no romper si aún no se ha creado."""
    try:
        execute_read(f"SELECT 1 FROM {nombre_tabla} LIMIT 1")
        return True
    except Exception:
        return False


# ═══════════════════════════════════════════════════════════════════════════
# ── CRUD DE UNIDADES ────────────────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════════════

# GET /api/unidades/
@router.get("/")
def listar_unidades(incluir_ocultas: bool = False, current_user=Depends(verify_token)):
    if incluir_ocultas:
        return execute_read("SELECT * FROM unidades ORDER BY id_lote, unit_number")
    return execute_read("SELECT * FROM unidades WHERE oculto=0 ORDER BY id_lote, unit_number")


@router.post("/")
def crear_unidad(unidad: UnidadCreate, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    existente = execute_read("SELECT id FROM unidades WHERE unit_number=%s", (unidad.unit_number,))
    if existente:
        execute_write(
            """UPDATE unidades SET
               id_lote=%s, vin_number=%s, reefer_serial=%s, reefer_model=%s,
               evaporator_serial_mjs11=%s, evaporator_model_1=%s,
               evaporator_serial_mjd22=%s, evaporator_model_2=%s, engine_serial=%s,
               compressor_serial=%s, generator_serial=%s, battery_charger_serial=%s
               WHERE unit_number=%s""",
            (unidad.id_lote, unidad.vin_number, unidad.reefer_serial, unidad.reefer_model,
             unidad.evaporator_serial_mjs11, unidad.evaporator_model_1,
             unidad.evaporator_serial_mjd22, unidad.evaporator_model_2, unidad.engine_serial,
             unidad.compressor_serial, unidad.generator_serial, unidad.battery_charger_serial,
             unidad.unit_number)
        )
        return {"mensaje": "Unidad actualizada"}
    else:
        ahora = datetime.now(TZ).replace(tzinfo=None)
        execute_write(
            """INSERT INTO unidades
               (unit_number, id_lote, vin_number, reefer_serial, reefer_model,
                evaporator_serial_mjs11, evaporator_model_1,
                evaporator_serial_mjd22, evaporator_model_2, engine_serial,
                compressor_serial, generator_serial, battery_charger_serial, fecha_registro)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (unidad.unit_number, unidad.id_lote, unidad.vin_number, unidad.reefer_serial,
             unidad.reefer_model, unidad.evaporator_serial_mjs11, unidad.evaporator_model_1,
             unidad.evaporator_serial_mjd22, unidad.evaporator_model_2,
             unidad.engine_serial, unidad.compressor_serial, unidad.generator_serial,
             unidad.battery_charger_serial, ahora)
        )
        return {"mensaje": "Unidad registrada"}


# PUT /api/unidades/series/update  — ANTES de /{unidad_id} para evitar colisión
@router.put("/series/update")
def actualizar_series(data: SeriesUpdate, current_user=Depends(verify_token)):
    campos = {k: v for k, v in data.dict().items() if k != "unit_number" and v is not None}
    if not campos:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")
    set_parts = ", ".join([f"{k}=%s" for k in campos])
    values = list(campos.values()) + [data.unit_number]
    execute_write(f"UPDATE unidades SET {set_parts} WHERE unit_number=%s", values)
    return {"mensaje": "Series actualizadas"}


# PUT /api/unidades/{unidad_id}
@router.put("/{unidad_id}")
def editar_unidad(unidad_id: int, unidad: UnidadCreate, current_user=Depends(verify_token)):
    if current_user["role"] not in ("admin", "lider"):
        raise HTTPException(status_code=403, detail="Solo administradores o líderes")

    actual = execute_read("SELECT unit_number FROM unidades WHERE id=%s", (unidad_id,))
    if not actual:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")
    numero_anterior = actual[0]["unit_number"]

    execute_write(
        """UPDATE unidades SET
           unit_number=%s, id_lote=%s, vin_number=%s, reefer_serial=%s, reefer_model=%s,
           evaporator_serial_mjs11=%s, evaporator_model_1=%s,
           evaporator_serial_mjd22=%s, evaporator_model_2=%s, engine_serial=%s,
           compressor_serial=%s, generator_serial=%s, battery_charger_serial=%s
           WHERE id=%s""",
        (unidad.unit_number, unidad.id_lote, unidad.vin_number, unidad.reefer_serial,
         unidad.reefer_model, unidad.evaporator_serial_mjs11, unidad.evaporator_model_1,
         unidad.evaporator_serial_mjd22, unidad.evaporator_model_2,
         unidad.engine_serial, unidad.compressor_serial, unidad.generator_serial,
         unidad.battery_charger_serial, unidad_id)
    )

    # Si el número de unidad cambió, cascadear el nuevo número a todo lo que
    # ya se trabajó con el número anterior, para no perder el historial.
    if numero_anterior != unidad.unit_number:
        execute_write("UPDATE asignaciones SET unidad=%s WHERE unidad=%s",
                       (unidad.unit_number, numero_anterior))
        execute_write("UPDATE evidencias SET unit_number=%s WHERE unit_number=%s",
                       (unidad.unit_number, numero_anterior))
        try:
            execute_write("UPDATE tickets SET unit_number=%s WHERE unit_number=%s",
                           (unidad.unit_number, numero_anterior))
        except Exception:
            pass  # tabla tickets puede no existir en instalaciones antiguas

    return {"mensaje": "Unidad actualizada"}


@router.post("/homologar")
def homologar_unidad(numero_anterior: str, numero_correcto: str, current_user=Depends(verify_token)):
    """
    Reasigna TODO el historial (asignaciones, evidencias, tickets) que haya quedado
    ligado a `numero_anterior` (p.ej. un número mal capturado) hacia `numero_correcto`.
    Úsalo cuando ya se registró una unidad duplicada por error de captura y quedaron
    dos números para la misma unidad física.
    """
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    if numero_anterior == numero_correcto:
        raise HTTPException(status_code=400, detail="Los números deben ser diferentes")

    destino = execute_read("SELECT id FROM unidades WHERE unit_number=%s", (numero_correcto,))
    if not destino:
        raise HTTPException(status_code=404, detail=f"No existe una unidad con el número {numero_correcto}")

    asig = execute_write("UPDATE asignaciones SET unidad=%s WHERE unidad=%s",
                          (numero_correcto, numero_anterior))
    evid = execute_write("UPDATE evidencias SET unit_number=%s WHERE unit_number=%s",
                          (numero_correcto, numero_anterior))
    tick = 0
    try:
        tick = execute_write("UPDATE tickets SET unit_number=%s WHERE unit_number=%s",
                              (numero_correcto, numero_anterior))
    except Exception:
        pass

    # Si además quedó un registro duplicado en `unidades` con el número viejo, lo eliminamos
    origen = execute_read("SELECT id FROM unidades WHERE unit_number=%s", (numero_anterior,))
    eliminado = False
    if origen:
        execute_write("DELETE FROM unidades WHERE unit_number=%s", (numero_anterior,))
        eliminado = True

    return {
        "mensaje": f"Historial de '{numero_anterior}' reasignado a '{numero_correcto}'",
        "asignaciones_migradas": asig,
        "evidencias_migradas": evid,
        "tickets_migrados": tick,
        "unidad_duplicada_eliminada": eliminado
    }


# DELETE /api/unidades/{unidad_id}
@router.delete("/{unidad_id}")
def eliminar_unidad(unidad_id: int, current_user=Depends(verify_token)):
    if current_user["role"] not in ("admin", "lider"):
        raise HTTPException(status_code=403, detail="Solo administradores o líderes")
    unidad = execute_read("SELECT unit_number FROM unidades WHERE id=%s", (unidad_id,))
    if not unidad:
        raise HTTPException(status_code=404, detail="Unidad no encontrada")
    unit_number = unidad[0]["unit_number"]
    execute_write("DELETE FROM evidencias WHERE unit_number=%s", (unit_number,))
    execute_write("DELETE FROM asignaciones WHERE unidad=%s", (unit_number,))
    execute_write("DELETE FROM unidades WHERE id=%s", (unidad_id,))
    return {"mensaje": "Unidad y sus datos relacionados eliminados"}


# ── REINICIAR CONTADOR DE HORAS 'CORRIENDO' (admin) ────────────────────────
@router.patch("/{unit_number}/reiniciar-corriendo")
def reiniciar_contador_corriendo(unit_number: str, current_user=Depends(verify_token)):
    """Pone en cero el contador acumulado de horas 'Corriendo' de una unidad
    (por ejemplo, después de darle servicio/mantenimiento)."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    import corriendo_tracking
    corriendo_tracking.reiniciar(unit_number)
    return {"mensaje": f"Contador de horas corriendo reiniciado para la unidad {unit_number}"}


# ── COMENTARIO LIBRE POR UNIDAD (nota del admin en el dashboard) ──────────
class ComentarioUnidadIn(BaseModel):
    comentario: Optional[str] = None


@router.patch("/{unit_number}/comentario")
def actualizar_comentario_unidad(unit_number: str, body: ComentarioUnidadIn, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    existentes = execute_read("SELECT id FROM unidades WHERE unit_number=%s", (unit_number,))
    if not existentes:
        raise HTTPException(status_code=404, detail=f"Unidad '{unit_number}' no encontrada")
    execute_write(
        "UPDATE unidades SET comentario=%s WHERE unit_number=%s",
        (body.comentario, unit_number)
    )
    return {"mensaje": f"Comentario actualizado para la unidad {unit_number}"}
