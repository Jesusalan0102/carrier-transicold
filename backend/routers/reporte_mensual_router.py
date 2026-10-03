"""
reporte_mensual_router.py
-------------------------
Datos del "Reporte final mensual — Indicadores por técnico".

Un *registro* es una de estas dos cosas dentro del mes consultado:
  • una actividad completada (asignaciones.estado = 'completada', por fecha_fin), o
  • un video subido como evidencia (evidencias.tipo = 'video', por created_at),
    que se cuenta como "Video liberación".

Cada registro cae en UNA sola categoría, por eso el total del mes es exactamente la
suma de las categorías y los porcentajes de la dona suman 100 %.

Si cambian los nombres de las actividades en el catálogo, basta con editar
CATEGORIAS (columna "actividades"): no hay que tocar nada más.
"""
import calendar
import logging
from datetime import date

from fastapi import APIRouter, Depends, HTTPException

from auth import verify_token
from db import execute_read

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/reporte-mensual", tags=["reporte-mensual"])

# clave estable, etiqueta que se muestra, actividad_id(s) de la tabla asignaciones
CATEGORIAS = [
    {"clave": "cableado",   "etiqueta": "Cableado",         "actividades": ["Cableado"]},
    {"clave": "cerrado",    "etiqueta": "Cerrado",          "actividades": ["Cerrado"]},
    {"clave": "accesorios", "etiqueta": "Accesorios",       "actividades": ["Accesorios"]},
    {"clave": "soldadura",  "etiqueta": "Soldadura",        "actividades": ["Soldadura"]},
    {"clave": "vacios",     "etiqueta": "Vacíos",           "actividades": ["Vacío"]},
    {"clave": "corrida",    "etiqueta": "Corrida",          "actividades": ["Horas Corridas", "Corriendo"]},
    {"clave": "series",     "etiqueta": "Series",           "actividades": ["Toma de Series"]},
    {"clave": "evidencia",  "etiqueta": "Evidencia final",  "actividades": ["Evidencia"]},
    {"clave": "video",      "etiqueta": "Video liberación", "actividades": []},   # viene de evidencias.tipo='video'
]

_ACT_A_CLAVE = {a: c["clave"] for c in CATEGORIAS for a in c["actividades"]}

MESES_ES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
            "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def _rango_mes(mes: str):
    """'2026-09' -> ('2026-09-01 00:00:00', '2026-10-01 00:00:00')"""
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


@router.get("/datos")
def datos_reporte_mensual(mes: str = "", current_user: dict = Depends(verify_token)):
    if current_user["role"] not in ("admin", "lider", "visor"):
        raise HTTPException(status_code=403, detail="Solo administradores, líderes y visores")

    if not mes:
        hoy = date.today()
        mes = f"{hoy.year}-{hoy.month:02d}"
    y, m, desde, hasta = _rango_mes(mes)

    # Técnicos: todos los usuarios con rol técnico/líder (aparecen aunque tengan 0 registros)
    usuarios = execute_read(
        "SELECT username, COALESCE(NULLIF(nombre_completo, ''), username) AS nombre "
        "FROM users WHERE role IN ('tecnico', 'lider') ORDER BY nombre"
    )
    tecnicos = {u["username"]: {"username": u["username"], "nombre": str(u["nombre"]).strip().upper(),
                                **{c["clave"]: 0 for c in CATEGORIAS}} for u in usuarios}

    # 1) Actividades completadas en el mes
    filas = execute_read(
        """
        SELECT a.tecnico, a.actividad_id, COUNT(*) AS n
        FROM asignaciones a
        INNER JOIN unidades u ON u.unit_number = a.unidad
        WHERE a.estado = 'completada'
          AND a.fecha_fin >= %s AND a.fecha_fin < %s
          AND u.oculto = 0
        GROUP BY a.tecnico, a.actividad_id
        """,
        (desde, hasta),
    )
    otras_actividades = 0
    for f in filas:
        clave = _ACT_A_CLAVE.get(f["actividad_id"])
        if clave is None:
            otras_actividades += int(f["n"])
            continue
        t = tecnicos.setdefault(f["tecnico"], {"username": f["tecnico"], "nombre": str(f["tecnico"]).upper(),
                                               **{c["clave"]: 0 for c in CATEGORIAS}})
        t[clave] += int(f["n"])

    # 2) Videos de evidencia subidos en el mes (Video liberación)
    try:
        videos = execute_read(
            "SELECT tecnico, COUNT(*) AS n FROM evidencias "
            "WHERE tipo = 'video' AND created_at >= %s AND created_at < %s GROUP BY tecnico",
            (desde, hasta),
        )
    except Exception as e:  # columna 'tipo' aún no migrada en la base
        logger.warning(f"[reporte-mensual] sin columna evidencias.tipo: {e}")
        videos = []
    for v in videos:
        if not v["tecnico"]:
            continue
        t = tecnicos.setdefault(v["tecnico"], {"username": v["tecnico"], "nombre": str(v["tecnico"]).upper(),
                                               **{c["clave"]: 0 for c in CATEGORIAS}})
        t["video"] += int(v["n"])

    lista = list(tecnicos.values())
    for t in lista:
        t["total"] = sum(t[c["clave"]] for c in CATEGORIAS)
    # Orden de la tabla: alfabético (como el tablero de referencia); el gráfico usa el mismo orden.
    lista.sort(key=lambda t: t["nombre"])

    totales = {c["clave"]: sum(t[c["clave"]] for t in lista) for c in CATEGORIAS}
    total = sum(totales.values())

    # Porcentajes a 1 decimal que suman exactamente 100.0 (método del mayor residuo)
    pct = {c["clave"]: 0.0 for c in CATEGORIAS}
    if total:
        crudos = {k: totales[k] * 1000 / total for k in totales}          # en décimas de punto
        base = {k: int(v) for k, v in crudos.items()}
        faltan = 1000 - sum(base.values())
        for k in sorted(crudos, key=lambda k: crudos[k] - base[k], reverse=True)[:faltan]:
            base[k] += 1
        pct = {k: base[k] / 10 for k in base}

    categorias = [
        {"clave": c["clave"], "etiqueta": c["etiqueta"], "total": totales[c["clave"]], "porcentaje": pct[c["clave"]]}
        for c in CATEGORIAS
    ]

    mayor_act = max(categorias, key=lambda c: c["total"]) if total else None
    mayor_tec = max(lista, key=lambda t: t["total"]) if total else None

    # Concentración: cuántos técnicos explican más de la mitad de los registros
    acumulado, n_top = 0, 0
    for t in sorted(lista, key=lambda t: t["total"], reverse=True):
        if total and acumulado < total / 2:
            acumulado += t["total"]
            n_top += 1

    return {
        "mes": f"{y}-{m:02d}",
        "mes_nombre": MESES_ES[m - 1].capitalize(),
        "anio": y,
        "dias_mes": calendar.monthrange(y, m)[1],
        "total": total,
        "otras_actividades": otras_actividades,
        "categorias": categorias,
        "tecnicos": lista,
        "n_tecnicos": len(lista),
        "n_tecnicos_activos": sum(1 for t in lista if t["total"] > 0),
        "actividad_mayor": {"etiqueta": mayor_act["etiqueta"], "total": mayor_act["total"]} if mayor_act else None,
        "tecnico_mayor": {"nombre": mayor_tec["nombre"], "total": mayor_tec["total"]} if mayor_tec else None,
        "concentracion": {
            "n_tecnicos_mitad": n_top,
            "porcentaje_mayor": round(mayor_tec["total"] / total * 100, 1) if mayor_tec and total else 0.0,
        },
    }
