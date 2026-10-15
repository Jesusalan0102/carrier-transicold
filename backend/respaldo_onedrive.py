"""
Respaldo diario de la BASE DE DATOS en OneDrive.

Qué guarda: TODAS las tablas (tareas, usuarios, evidencias con sus enlaces a OneDrive, etc.) en un ZIP
  carrier-transicold/Respaldos/respaldo_AAAA-MM-DD_HHMM.zip
con un archivo .jsonl por tabla (una fila por línea, conserva NULL y tipos) y esquema.sql.
Qué NO guarda: el contenido binario de los archivos (columnas BLOB y la tabla evidencia_partes): las fotos y
videos ya tienen su copia en OneDrive y meterlos aquí haría el respaldo enorme. Con este ZIP + las carpetas de
Evidencias de OneDrive se puede reconstruir todo: cada fila de `evidencias` conserva el id del archivo en OneDrive.
Se conservan los últimos 14 respaldos. Lo dispara el monitor de salud (cada ~24 h) o el admin a mano.
"""
import io
import json
import logging
import os
import re
import tempfile
import time
import zipfile
from datetime import datetime

from db import execute_read

logger = logging.getLogger(__name__)

RETENER = 14
EXCLUIR_TABLAS = {"evidencia_partes", "salud_sistema"}     # binarios / estado interno
FILAS_POR_LOTE = 2000
MAX_ZIP_MB = 200                                            # tope de seguridad antes de subir
_NOMBRE_OK = re.compile(r"^[\w$]+$")


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
                    "  los archivos viven en OneDrive/carrier-transicold/Evidencias y cada fila de 'evidencias'\n"
                    "  guarda su onedrive_item_id para volver a enlazarlos.\n"
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
