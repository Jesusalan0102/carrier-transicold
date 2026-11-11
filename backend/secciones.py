"""
secciones.py — secciones de evidencia (Reefer / Evaporador / Blower / Tanque) por lote.

Las tareas "Inspección" y "Evidencia" se pueden dividir en secciones. El administrador elige, POR LOTE,
cuáles secciones se habilitan (lotes_config.secciones_evidencia); esa elección aplica a todas las unidades
del lote. Cada evidencia guarda la sección con la que se tomó (evidencias.seccion) y la exportación del lote
crea una subcarpeta por sección dentro de la carpeta de la tarea:

    evidencias/<lote>/<VIN>/Inspección/Reefer/…      evidencias/<lote>/<VIN>/Evidencia/Tanque/…

Las evidencias de otras tareas (o anteriores a esta función) no llevan sección y se exportan como siempre.
"""
import logging

logger = logging.getLogger(__name__)

# Orden canónico (el mismo en la pantalla del administrador, la del técnico y la exportación).
SECCIONES = ("reefer", "evaporador", "blower", "tanque")
ETIQUETAS = {"reefer": "Reefer", "evaporador": "Evaporador", "blower": "Blower", "tanque": "Tanque"}

# Tareas que se dividen en secciones.
ACTIVIDADES_CON_SECCIONES = ("Inspección", "Evidencia")


def _como_lista(valores) -> list:
    if valores is None:
        return []
    if isinstance(valores, str):
        valores = valores.split(",")
    return [str(v).strip().lower() for v in valores if str(v).strip()]


def invalidas(valores) -> list:
    """Nombres que NO son una sección conocida (para rechazar la petición con un mensaje claro)."""
    return [v for v in _como_lista(valores) if v not in SECCIONES]


def normalizar(valores) -> list:
    """Lista de secciones válidas, sin repetidas y en el orden canónico. Acepta lista o 'a,b,c'."""
    pedidas = set(_como_lista(valores))
    return [s for s in SECCIONES if s in pedidas]


def a_texto(valores) -> "str | None":
    """Formato guardado en la base de datos ('reefer,tanque'); None si no hay ninguna."""
    lista = normalizar(valores)
    return ",".join(lista) if lista else None


def seccion_valida(valor) -> "str | None":
    v = str(valor or "").strip().lower()
    return v if v in SECCIONES else None


def etiqueta(seccion) -> "str | None":
    """Nombre de la carpeta/etiqueta ('Reefer') o None si no es una sección válida."""
    s = seccion_valida(seccion)
    return ETIQUETAS[s] if s else None


def aplica_a_actividad(actividad) -> bool:
    return (actividad or "").strip() in ACTIVIDADES_CON_SECCIONES


# ── base de datos (import perezoso: así se puede probar sin conexión) ──────────────────────────
def secciones_de_lote(id_lote: str) -> list:
    """Secciones habilitadas por el administrador para el lote ([] si no ha elegido ninguna)."""
    from db import execute_read
    if not (id_lote or "").strip():
        return []
    try:
        filas = execute_read("SELECT secciones_evidencia FROM lotes_config WHERE id_lote=%s", (id_lote,)) or []
    except Exception as e:      # columna aún no migrada: la app sigue funcionando sin secciones
        logger.warning(f"[secciones] no se pudo leer la configuración del lote {id_lote}: {e}")
        return []
    return normalizar(filas[0]["secciones_evidencia"]) if filas else []


def guardar_secciones_lote(id_lote: str, secciones, usuario: str) -> list:
    """Guarda la selección (sin tocar tipo_reefer) y devuelve la lista normalizada. Vacía = sin secciones."""
    from db import execute_write
    lista = normalizar(secciones)
    execute_write(
        "INSERT INTO lotes_config (id_lote, secciones_evidencia, updated_by) VALUES (%s,%s,%s) "
        "ON DUPLICATE KEY UPDATE secciones_evidencia=VALUES(secciones_evidencia), updated_by=VALUES(updated_by)",
        (id_lote, a_texto(lista), usuario),
    )
    return lista


def info_asignacion(asignacion_id: int) -> "dict | None":
    """Datos de la tarea necesarios para decidir si lleva secciones:
    {'actividad', 'tecnico', 'id_lote', 'aplica', 'secciones'}  (None si la tarea no existe)."""
    from db import execute_read
    filas = execute_read(
        "SELECT a.actividad_id AS actividad, a.tecnico AS tecnico, "
        "(SELECT u.id_lote FROM unidades u WHERE u.unit_number = a.unidad LIMIT 1) AS id_lote "
        "FROM asignaciones a WHERE a.id=%s",
        (asignacion_id,),
    )
    if not filas:
        return None
    f = filas[0]
    aplica = aplica_a_actividad(f["actividad"])
    return {
        "actividad": f["actividad"],
        "tecnico": f["tecnico"],
        "id_lote": f["id_lote"],
        "aplica": aplica,
        "secciones": secciones_de_lote(f["id_lote"]) if aplica else [],
    }


def seccion_para_guardar(asignacion_id, seccion) -> "str | None":
    """Qué sección se guarda con una evidencia que llega al servidor.

    • Sin sección (o sin tarea) → None.   • Nombre desconocido → ValueError (la petición es un error).
    • Sección válida pero la tarea NO es Inspección/Evidencia → None (se ignora, no se pierde la evidencia).
    Nota: NO se exige que la sección siga habilitada en el lote: una foto tomada sin señal y subida horas
    después no se debe perder si el administrador cambió la selección entretanto."""
    if seccion is None or str(seccion).strip() == "":
        return None
    valida = seccion_valida(seccion)
    if not valida:
        raise ValueError(f"Sección no válida: '{seccion}'. Opciones: {', '.join(SECCIONES)}")
    if asignacion_id is None:
        return None
    info = info_asignacion(int(asignacion_id))
    return valida if (info and info["aplica"]) else None
