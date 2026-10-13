"""
Respaldo en la base de datos para archivos GRANDES de evidencia.

La base (TiDB) rechaza cualquier fila de más de ~6 MB:
    (8025, 'entry too large, the max entry size is 6291456 ...')
Por eso un video de 11 MB no se podía guardar como respaldo cuando OneDrive fallaba.
Aquí el archivo se parte en trozos de 4 MB (tabla evidencia_partes) y se reconstruye
al servirlo o al armar un ZIP. La fila de `evidencias` queda con contenido NULL.
"""
import logging
from db import execute_read, execute_write

logger = logging.getLogger(__name__)

PARTE_BYTES = 4 * 1024 * 1024          # cada trozo cabe sobrado en el límite de 6 MB por fila
DB_FILA_MAX = 5 * 1024 * 1024          # arriba de esto NO se guarda en una sola fila


def guardar_partes(evidencia_id: int, contenido: bytes) -> int:
    n = 0
    for i in range(0, len(contenido), PARTE_BYTES):
        execute_write(
            "INSERT INTO evidencia_partes (evidencia_id, orden, contenido) VALUES (%s,%s,%s)",
            (evidencia_id, n, contenido[i:i + PARTE_BYTES]),
        )
        n += 1
    return n


def borrar_partes(ids: list) -> None:
    if not ids:
        return
    ph = ",".join(["%s"] * len(ids))
    execute_write(f"DELETE FROM evidencia_partes WHERE evidencia_id IN ({ph})", tuple(ids))


def _tamanos(evidencia_id: int):
    filas = execute_read(
        "SELECT orden, LENGTH(contenido) AS n FROM evidencia_partes WHERE evidencia_id=%s ORDER BY orden",
        (evidencia_id,),
    ) or []
    return [(f["orden"], int(f["n"] or 0)) for f in filas]


def tamano_total(evidencia_id: int) -> int:
    """0 si el archivo no está guardado en partes."""
    try:
        return sum(n for _, n in _tamanos(evidencia_id))
    except Exception as e:           # tabla aún no creada
        logger.warning(f"[partes] no se pudo consultar evidencia {evidencia_id}: {e}")
        return 0


def iterar_rango(evidencia_id: int, inicio: int, fin: int):
    """Entrega los bytes [inicio, fin] leyendo solo los trozos que hacen falta."""
    cursor = 0
    for orden, n in _tamanos(evidencia_id):
        trozo_ini, trozo_fin = cursor, cursor + n - 1
        cursor += n
        if trozo_fin < inicio:
            continue
        if trozo_ini > fin:
            break
        fila = execute_read(
            "SELECT contenido FROM evidencia_partes WHERE evidencia_id=%s AND orden=%s", (evidencia_id, orden)
        )
        datos = bytes(fila[0]["contenido"]) if fila and fila[0]["contenido"] else b""
        yield datos[max(inicio - trozo_ini, 0): fin - trozo_ini + 1]


def leer_partes(evidencia_id: int):
    """Archivo completo en bytes, o None si no está guardado en partes."""
    total = tamano_total(evidencia_id)
    if not total:
        return None
    return b"".join(iterar_rango(evidencia_id, 0, total - 1))
