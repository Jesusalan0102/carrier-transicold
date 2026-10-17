"""
Respaldo diario de la BASE DE DATOS en OneDrive.

Qué guarda: TODAS las tablas (tareas, usuarios, evidencias con sus enlaces a OneDrive, etc.) en un ZIP
  carrier-transicold/Respaldos/respaldo_AAAA-MM-DD_HHMM.zip
con un archivo .jsonl por tabla (una fila por línea, conserva NULL y tipos) y esquema.sql.
Qué NO guarda en el ZIP: el contenido binario de los archivos (columnas BLOB y la tabla evidencia_partes), para que
no sea enorme. Las fotos y videos que estén solo en la DB los copia `respaldo_evidencias.respaldar_evidencias`
(se llama justo después, cada noche) a sus carpetas de Evidencias/<lote>/<unidad>_<serie>/ sin duplicar nada.
Con este ZIP + las carpetas de Evidencias de OneDrive se puede reconstruir todo.
Se conservan los últimos 14 respaldos.
Lo dispara `programador_respaldo_nocturno` (todas las noches a HORA_RESPALDO, hora de Tijuana; variable de
entorno RESPALDO_HORA), con reintentos y aviso push a los admins si falla. El monitor de salud queda como
red de seguridad (si pasan >30 h sin respaldo bueno) y el admin puede lanzarlo a mano.
"""
import io
import json
import logging
import os
import re
import tempfile
import time
import zipfile
import asyncio
from datetime import datetime, timedelta

from db import execute_read

logger = logging.getLogger(__name__)

RETENER = 14
EXCLUIR_TABLAS = {"evidencia_partes", "salud_sistema"}     # binarios / estado interno
FILAS_POR_LOTE = 2000
MAX_ZIP_MB = 200                                            # tope de seguridad antes de subir
_NOMBRE_OK = re.compile(r"^[\w$]+$")

# ── programación nocturna ──────────────────────────────────────────────────
def _hora_respaldo() -> int:
    try:
        return min(23, max(0, int(os.getenv("RESPALDO_HORA", "2"))))
    except ValueError:
        return 2
REINTENTOS = 3                          # intentos por noche
ESPERA_REINTENTO_SEG = 30 * 60          # entre intentos
MIN_HORAS_ENTRE_RESPALDOS = 12          # evita duplicados (redeploys, relojes)


def _tablas() -> list:
    filas = execute_read("SHOW TABLES") or []
    out = [str(list(f.values())[0]) for f in filas]
    return [t for t in out if _NOMBRE_OK.match(t) and t not in EXCLUIR_TABLAS]


def _columnas(tabla: str) -> list:
    """Columnas NO binarias (los blobs no van al respaldo)."""
    cols = execute_read(f"SHOW COLUMNS FROM `{tabla}`") or []
    return [c["Field"] for c in cols if "blob" not in str(c.get("Type", "")).lower()
            and "binary" not in str(c.get("Type", "")).lower()]


def _orden(tabla: str) -> str:
    """ORDER BY por la llave primaria, para paginar sin perder ni repetir filas."""
    try:
        ks = execute_read(f"SHOW KEYS FROM `{tabla}` WHERE Key_name='PRIMARY'") or []
        pk = [k["Column_name"] for k in sorted(ks, key=lambda k: int(k.get("Seq_in_index", 0)))]
        return " ORDER BY " + ", ".join(f"`{c}`" for c in pk) if pk else ""
    except Exception:
        return ""


def _serializar(v):
    if isinstance(v, (bytes, bytearray, memoryview)):
        return None                                        # no debería pasar (se excluyen los blobs)
    return str(v) if not isinstance(v, (int, float, str, bool, type(None))) else v


def generar_zip(ruta_zip: str) -> dict:
    """Escribe el ZIP en disco, tabla por tabla y por lotes (no carga tablas enteras en RAM)."""
    resumen = {"tablas": 0, "filas": 0, "detalle": {}}
    with zipfile.ZipFile(ruta_zip, "w", zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        esquema = []
        for tabla in _tablas():
            try:
                cr = execute_read(f"SHOW CREATE TABLE `{tabla}`") or []
                if cr:
                    esquema.append(list(cr[0].values())[1] + ";\n")
                cols = _columnas(tabla)
                if not cols:
                    continue
                sel = ", ".join(f"`{c}`" for c in cols)
                orden = _orden(tabla)
                n, offset = 0, 0
                with zf.open(f"{tabla}.jsonl", "w", force_zip64=True) as dest:
                    while True:
                        lote = execute_read(f"SELECT {sel} FROM `{tabla}`{orden} LIMIT {FILAS_POR_LOTE} OFFSET {offset}") or []
                        if not lote:
                            break
                        for fila in lote:
                            dest.write((json.dumps({k: _serializar(v) for k, v in fila.items()}, ensure_ascii=False) + "\n").encode("utf-8"))
                        n += len(lote)
                        offset += FILAS_POR_LOTE
                        if len(lote) < FILAS_POR_LOTE:
                            break
                resumen["detalle"][tabla] = n
                resumen["tablas"] += 1
                resumen["filas"] += n
            except Exception as e:                          # una tabla rota no debe tirar todo el respaldo
                logger.error(f"[respaldo] tabla {tabla}: {e}")
                resumen["detalle"][tabla] = f"ERROR: {str(e)[:80]}"
        zf.writestr("esquema.sql", "-- Estructura de las tablas (SHOW CREATE TABLE)\n" + "\n".join(esquema))
        zf.writestr("LEEME.txt",
                    "Respaldo de la base de datos Carrier Transicold\n"
                    f"Generado: {datetime.now().isoformat(timespec='seconds')}\n\n"
                    "- <tabla>.jsonl : una fila por línea (JSON). NULL se conserva como null.\n"
                    "- esquema.sql   : CREATE TABLE de cada tabla.\n"
                    "- NO incluye el contenido binario de fotos/videos (columna 'contenido' ni evidencia_partes):\n"
                    "  el respaldo nocturno los copia aparte a OneDrive/carrier-transicold/Evidencias/<lote>/<unidad>_<serie>/\n"
                    "  (mismo orden de carpetas que la app; sin duplicados).\n"
                    "- Contiene datos sensibles (usuarios, hashes de contraseña). No lo compartas.\n")
    return resumen


def _aplicar_retencion(carpeta: str) -> int:
    """Borra los respaldos más viejos, dejando los últimos RETENER."""
    import requests
    import onedrive_service as od
    r = requests.get(f"{od.GRAPH_BASE}/me/drive/root:/{carpeta}:/children?$top=200&$select=id,name",
                     headers={"Authorization": f"Bearer {od._get_token()}"}, timeout=30)
    r.raise_for_status()
    nombres = sorted([x for x in r.json().get("value", []) if re.match(r"^respaldo_\d{4}-\d{2}-\d{2}_\d{4}\.zip$", x["name"])],
                     key=lambda x: x["name"], reverse=True)
    borrados = 0
    for viejo in nombres[RETENER:]:
        try:
            od._borrar_item(viejo["id"])
            borrados += 1
        except Exception as e:
            logger.warning(f"[respaldo] no se pudo borrar {viejo['name']}: {e}")
    return borrados


def ejecutar_respaldo() -> dict:
    """Genera el ZIP, lo sube a OneDrive, VERIFICA el tamaño y aplica la retención. Nunca lanza excepción."""
    import onedrive_service as od
    inicio = time.time()
    tmp = tempfile.NamedTemporaryFile(prefix="respaldo_", suffix=".zip", delete=False)
    tmp.close()
    try:
        resumen = generar_zip(tmp.name)
        tam = os.path.getsize(tmp.name)
        if tam > MAX_ZIP_MB * 1048576:
            return {"ok": False, "error": f"El respaldo pesa {tam // 1048576} MB (más de {MAX_ZIP_MB} MB): no se subió", "ts": time.time()}
        nombre = f"respaldo_{datetime.now(od.TZ).strftime('%Y-%m-%d_%H%M')}.zip"
        carpeta = f"{od.BASE_FOLDER}/Respaldos"
        od._upload_with_retry(od._ensure_folder, carpeta)
        with open(tmp.name, "rb") as fh:
            contenido = fh.read()
        res = od.upload_large_file(contenido, f"{carpeta}/{nombre}", "application/zip")
        item_id = res.get("id") or res.get("item_id")
        if item_id and od.tamano_item(item_id) != len(contenido):
            return {"ok": False, "error": "El tamaño en OneDrive no coincide: el respaldo quedó incompleto", "ts": time.time()}
        borrados = 0
        try:
            borrados = _aplicar_retencion(carpeta)
        except Exception as e:
            logger.warning(f"[respaldo] retención falló: {e}")
        errores = {t: v for t, v in resumen["detalle"].items() if isinstance(v, str)}
        return {"ok": not errores, "ts": time.time(), "archivo": nombre, "mb": round(tam / 1048576, 2),
                "tablas": resumen["tablas"], "filas": resumen["filas"], "antiguos_borrados": borrados,
                "segundos": round(time.time() - inicio, 1),
                **({"error": f"{len(errores)} tabla(s) con error: {', '.join(errores)}"} if errores else {})}
    except Exception as e:
        logger.error(f"[respaldo] falló: {e}")
        return {"ok": False, "error": str(e)[:300], "ts": time.time()}
    finally:
        try:
            os.remove(tmp.name)
        except OSError:
            pass


# ═══ Programación nocturna ═══════════════════════════════════════════════════
def segundos_hasta_hora(hora: int, ahora: datetime) -> float:
    """Segundos hasta la próxima ocurrencia de HH:00 en la zona horaria de `ahora`."""
    objetivo = ahora.replace(hour=hora, minute=0, second=0, microsecond=0)
    if objetivo <= ahora:
        objetivo += timedelta(days=1)
    return (objetivo - ahora).total_seconds()


async def ejecutar_nocturno() -> dict:
    """Un respaldo de la noche: omite si ya hay uno bueno reciente, reintenta y avisa si todo falla."""
    from fastapi.concurrency import run_in_threadpool
    import salud_evidencias as sv
    previo = sv.leer_estado("respaldo") or {}
    if previo.get("ts_ok") and (time.time() - float(previo["ts_ok"])) < MIN_HORAS_ENTRE_RESPALDOS * 3600:
        return {"omitido": True}
    r: dict = {}
    for intento in range(1, REINTENTOS + 1):
        try:
            r = await run_in_threadpool(sv.respaldar)
        except Exception as e:
            r = {"ok": False, "error": str(e)[:300]}
        if r.get("ok"):
            logger.info(f"[respaldo] nocturno OK en el intento {intento}: {r.get('archivo')}")
            return await run_in_threadpool(_respaldar_fotos_y_videos, r)
        logger.warning(f"[respaldo] nocturno intento {intento}/{REINTENTOS} falló: {r.get('error')}")
        if intento < REINTENTOS:
            await asyncio.sleep(ESPERA_REINTENTO_SEG)
    sv._avisar_admins("⚠️ Respaldo nocturno falló",
                      f"{REINTENTOS} intentos sin éxito: {str(r.get('error', ''))[:140]}")
    return await run_in_threadpool(_respaldar_fotos_y_videos, r)


def _respaldar_fotos_y_videos(r: dict) -> dict:
    """Segunda parte de la noche: fotos/videos que están solo en la DB -> su carpeta de OneDrive."""
    import salud_evidencias as sv
    from respaldo_evidencias import respaldar_evidencias
    try:
        ev = respaldar_evidencias(aplicar=True)
    except Exception as e:
        ev = {"ok": False, "completo": False, "errores": [{"error": str(e)[:200]}]}
    ev["ts"] = time.time()
    try:
        sv.guardar_estado("respaldo_evidencias", ev)
    except Exception as e:
        logger.warning(f"[respaldo] no se pudo guardar el estado de evidencias: {e}")
    if not ev.get("ok"):
        primero = (ev.get("errores") or [{}])[0].get("error") or ("quedó incompleto (se sigue mañana)" if not ev.get("completo") else "")
        sv._avisar_admins("⚠️ Respaldo de fotos y videos", f"{len(ev.get('errores') or [])} error(es). {str(primero)[:140]}")
    r["evidencias"] = ev
    return r


async def programador_respaldo_nocturno():
    """Tarea de fondo (se registra en el startup de main.py): corre cada noche a RESPALDO_HORA (Tijuana)."""
    import onedrive_service as od
    while True:
        try:
            await asyncio.sleep(segundos_hasta_hora(_hora_respaldo(), datetime.now(od.TZ)))
            await ejecutar_nocturno()
            await asyncio.sleep(120)        # nunca dos veces en el mismo minuto
        except asyncio.CancelledError:
            raise
        except Exception as e:              # el programador nunca debe morir
            logger.error(f"[respaldo] programador: {e}")
            await asyncio.sleep(300)
