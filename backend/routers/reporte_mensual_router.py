"""
reporte_mensual_router.py
-------------------------
Datos del "Reporte final mensual — Indicadores por técnico".

El reporte se alimenta de las MISMAS tareas que los técnicos tienen registradas en la app:

  • Tareas asignadas (tabla asignaciones) que quedaron en estado 'completada' durante el mes
    (por fecha_fin; si una tarea antigua no tiene fecha_fin se usa fecha_inicio).
  • Las categorías NO están escritas a mano: salen del catálogo real de actividades
    (tabla actividades_catalogo, el mismo que usa "Asignación por cluster"), en el mismo orden.
  • Los tickets (asignaciones llamadas "Ticket #N") se agrupan en una sola categoría "Tickets".
  • Si aparece una tarea con un nombre que ya no está en el catálogo (actividad renombrada o
    eliminada), se cuenta con su propio nombre: ninguna tarea registrada se pierde ni se manda a "otros".
  • Videos subidos como evidencia (evidencias.tipo = 'video') -> categoría "Video liberación".

Filtros iguales a los del dashboard ejecutivo: se excluyen las unidades de lotes ocultos
(unidades.oculto = 1). A diferencia del dashboard, las tareas cuya unidad no existe en la tabla
unidades (por ejemplo, tickets sobre una unidad no capturada) SÍ cuentan.

Cada registro cae en UNA sola categoría, así que el total del mes es exactamente la suma de las
categorías y los porcentajes de la dona suman 100.0 %.
"""
import calendar
import logging
import re
import unicodedata
from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from auth import verify_token
from db import execute_read

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reporte-mensual", tags=["reporte-mensual"])

# Respaldo por si la tabla actividades_catalogo no existe todavía (mismo orden que db.py)
CATALOGO_RESPALDO = [
    "Cableado", "Programación", "Soldadura", "Check de fugas", "Vacío", "Cerrado", "Pre-viaje",
    "Horas Corridas", "Standby", "GPS", "Corriendo", "Inspección", "Accesorios", "Toma de Valores",
    "Evidencia", "Toma de Series", "Extra Eléctrico", "Extra Soldador",
    "Retrabajo Eléctrico", "Retrabajo Soldador",
]

ETIQUETA_TICKETS = "Tickets"
ETIQUETA_VIDEO = "Video liberación"
CLAVE_VIDEO = "video_liberacion"

MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
            "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def _sin_acentos(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")


def _clave(nombre: str) -> str:
    """'Check de fugas' -> 'check_de_fugas' (estable aunque cambie la capitalización o los acentos)."""
    k = re.sub(r"[^a-z0-9]+", "_", _sin_acentos(str(nombre)).lower()).strip("_")
    return k or "sin_nombre"


def _rango_mes(mes: str):
    """'2026-09' -> (2026, 9, '2026-09-01 00:00:00', '2026-10-01 00:00:00')"""
    try:
        y, m = mes.split("-")
        y, m = int(y), int(m)
        if not (2000 <= y <= 2100 and 1 <= m <= 12):
            raise ValueError
    except Exception:
        raise HTTPException(status_code=400, detail="Parámetro 'mes' inválido. Usa el formato AAAA-MM.")
    ini = date(y, m, 1)
    fin = date(y + (m == 12), (m % 12) + 1, 1)
    return y, m, f"{ini.isoformat()} 00:00:00", f"{fin.isoformat()} 00:00:00"


def _nombre_categoria(actividad_id, catalogo_por_clave: dict) -> str:
    """Nombre con el que se cuenta una tarea registrada."""
    nombre = " ".join(str(actividad_id or "").split())
    if not nombre:
        return "Sin actividad"
    if re.match(r"^ticket\b", nombre, re.IGNORECASE):          # 'Ticket #12' -> 'Tickets'
        return ETIQUETA_TICKETS
    return catalogo_por_clave.get(_clave(nombre), nombre)       # nombre del catálogo, o el propio si ya no existe


@router.get("/datos")
def datos_reporte_mensual(mes: str = "", current_user: dict = Depends(verify_token)):
    if current_user["role"] not in ("admin", "lider", "visor"):
        raise HTTPException(status_code=403, detail="Solo administradores, líderes y visores")

    if not mes:
        hoy = date.today()
        mes = f"{hoy.year}-{hoy.month:02d}"
    y, m, desde, hasta = _rango_mes(mes)

    # ── 1) Catálogo real de actividades (orden = orden del catálogo) ───────────────
    try:
        filas_cat = execute_read("SELECT nombre, activo FROM actividades_catalogo ORDER BY id")
        catalogo = [(str(f["nombre"]).strip(), bool(f["activo"])) for f in filas_cat if f.get("nombre")]
    except Exception as e:
        logger.warning(f"[reporte-mensual] sin catálogo de actividades, se usa el de respaldo: {e}")
        catalogo = []
    if not catalogo:
        catalogo = [(n, True) for n in CATALOGO_RESPALDO]
    catalogo_por_clave = {_clave(n): n for n, _ in catalogo}

    # ── 2) Técnicos: nombres de todos los usuarios + plantilla (tecnico/lider) ──────
    usuarios = execute_read(
        "SELECT username, role, COALESCE(NULLIF(nombre_completo, ''), username) AS nombre FROM users"
    )
    nombre_de = {u["username"]: str(u["nombre"]).strip().upper() for u in usuarios}
    plantilla = [u["username"] for u in usuarios if u.get("role") in ("tecnico", "lider")]

    # ── 3) Tareas completadas en el mes ─────────────────────────────────────────────
    filas = execute_read(
        """
        SELECT a.tecnico, a.actividad_id, COUNT(*) AS n
        FROM asignaciones a
        LEFT JOIN unidades u ON u.unit_number = a.unidad
        WHERE a.estado = 'completada'
          AND COALESCE(a.fecha_fin, a.fecha_inicio) >= %s
          AND COALESCE(a.fecha_fin, a.fecha_inicio) <  %s
          AND (u.oculto IS NULL OR u.oculto = 0)
        GROUP BY a.tecnico, a.actividad_id
        """,
        (desde, hasta),
    )

    # ── 4) Videos de evidencia del mes (Video liberación) ───────────────────────────
    try:
        videos = execute_read(
            "SELECT tecnico, COUNT(*) AS n FROM evidencias "
            "WHERE tipo = 'video' AND created_at >= %s AND created_at < %s GROUP BY tecnico",
            (desde, hasta),
        )
    except Exception as e:  # columna 'tipo' aún no migrada en la base
        logger.warning(f"[reporte-mensual] sin columna evidencias.tipo: {e}")
        videos = []

    # ── 5) Acumular por técnico y por categoría ─────────────────────────────────────
    conteo = {}                 # {username: {nombre_categoria: n}}
    totales_cat = {}            # {nombre_categoria: n}
    for f in filas:
        if not f["tecnico"]:
            continue
        cat = _nombre_categoria(f["actividad_id"], catalogo_por_clave)
        n = int(f["n"])
        conteo.setdefault(f["tecnico"], {})
        conteo[f["tecnico"]][cat] = conteo[f["tecnico"]].get(cat, 0) + n
        totales_cat[cat] = totales_cat.get(cat, 0) + n
    for v in videos:
        if not v["tecnico"]:
            continue
        n = int(v["n"])
        conteo.setdefault(v["tecnico"], {})
        conteo[v["tecnico"]][ETIQUETA_VIDEO] = conteo[v["tecnico"]].get(ETIQUETA_VIDEO, 0) + n
        totales_cat[ETIQUETA_VIDEO] = totales_cat.get(ETIQUETA_VIDEO, 0) + n

    # ── 6) Orden de categorías: catálogo -> Tickets -> otras (por nombre) -> Video ──
    orden_nombres = [n for n, _ in catalogo]
    extras = sorted(c for c in totales_cat
                    if c not in orden_nombres and c not in (ETIQUETA_TICKETS, ETIQUETA_VIDEO))
    orden_nombres += [ETIQUETA_TICKETS] + extras + [ETIQUETA_VIDEO]
    orden_de = {n: i for i, n in enumerate(orden_nombres)}

    total = sum(totales_cat.values())

    # Porcentajes a 1 decimal que suman exactamente 100.0 (método del mayor residuo)
    pct = {}
    if total:
        crudos = {c: t * 1000 / total for c, t in totales_cat.items()}
        base = {c: int(v) for c, v in crudos.items()}
        faltan = 1000 - sum(base.values())
        for c in sorted(crudos, key=lambda c: crudos[c] - base[c], reverse=True)[:faltan]:
            base[c] += 1
        pct = {c: base[c] / 10 for c in base}

    # Solo se muestran las categorías con registros en el mes; las del catálogo activo sin
    # registros se listan aparte para que se vea que sí se consideraron.
    categorias = []
    for nombre in sorted((c for c, t in totales_cat.items() if t > 0), key=lambda c: orden_de.get(c, 10_000)):
        categorias.append({
            "clave": CLAVE_VIDEO if nombre == ETIQUETA_VIDEO else _clave(nombre),
            "etiqueta": nombre,
            "orden": orden_de.get(nombre, 10_000),
            "total": totales_cat[nombre],
            "porcentaje": pct.get(nombre, 0.0),
        })
    sin_registros = [n for n, activo in catalogo if activo and totales_cat.get(n, 0) == 0]

    # ── 7) Filas por técnico ────────────────────────────────────────────────────────
    usernames = list(dict.fromkeys(plantilla + list(conteo.keys())))
    tecnicos = []
    for u in usernames:
        fila = {"username": u, "nombre": nombre_de.get(u, str(u).upper())}
        for c in categorias:
            fila[c["clave"]] = conteo.get(u, {}).get(c["etiqueta"], 0)
        fila["total"] = sum(conteo.get(u, {}).values())
        tecnicos.append(fila)
    tecnicos.sort(key=lambda t: t["nombre"])       # alfabético, como el tablero de referencia

    mayor_act = max(categorias, key=lambda c: c["total"]) if categorias else None
    mayor_tec = max(tecnicos, key=lambda t: t["total"]) if tecnicos and total else None

    # Concentración: cuántos técnicos explican más de la mitad de los registros
    acumulado, n_top = 0, 0
    for t in sorted(tecnicos, key=lambda t: t["total"], reverse=True):
        if total and acumulado < total / 2:
            acumulado += t["total"]
            n_top += 1

    return {
        "mes": f"{y}-{m:02d}",
        "mes_nombre": MESES_ES[m - 1].capitalize(),
        "anio": y,
        "dias_mes": calendar.monthrange(y, m)[1],
        "total": total,
        "categorias": categorias,
        "sin_registros": sin_registros,
        "tecnicos": tecnicos,
        "n_tecnicos": len(tecnicos),
        "n_tecnicos_activos": sum(1 for t in tecnicos if t["total"] > 0),
        "actividad_mayor": {"etiqueta": mayor_act["etiqueta"], "total": mayor_act["total"]} if mayor_act else None,
        "tecnico_mayor": {"nombre": mayor_tec["nombre"], "total": mayor_tec["total"]} if mayor_tec else None,
        "concentracion": {
            "n_tecnicos_mitad": n_top,
            "porcentaje_mayor": round(mayor_tec["total"] / total * 100, 1) if mayor_tec and total else 0.0,
        },
    }
