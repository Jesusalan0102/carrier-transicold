import io
from datetime import datetime
from zoneinfo import ZoneInfo
TZ = ZoneInfo("America/Tijuana")
import pymysql
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from db import get_db_connection, execute_read
from auth import verify_token

router = APIRouter(prefix="/reportes", tags=["Reportes Maestros"])

# ── Paleta corporativa ────────────────────────────────────────────────────────
AZUL_CORP   = "1F4E78"   # encabezados principales
AZUL_CLARO  = "2E75B6"   # encabezados secundarios
VERDE       = "375623"   # horarios / asistencia
AMARILLO    = "FFF2CC"   # retardo leve
ROJO_CLARO  = "FFDADA"   # retardo severo
GRIS_FILA   = "F2F2F2"   # filas alternas

def _hdr(color=AZUL_CORP):
    return {
        "font":      Font(name="Arial", size=10, bold=True, color="FFFFFF"),
        "fill":      PatternFill("solid", start_color=color, end_color=color),
        "alignment": Alignment(horizontal="center", vertical="center", wrap_text=True),
        "border":    Border(
            bottom=Side(style="thin", color="FFFFFF"),
            right=Side(style="thin", color="FFFFFF"),
        ),
    }

def _apply(cell, styles):
    for attr, val in styles.items():
        setattr(cell, attr, val)

def _autofit(ws, min_w=10, max_w=45):
    for col in ws.columns:
        length = max((len(str(c.value or "")) for c in col), default=0)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max(length + 2, min_w), max_w)

def _write_sheet(ws, columns, rows, hdr_color=AZUL_CORP, freeze=True):
    """Escribe encabezados + filas con formato alterno."""
    ws.append(columns)
    hstyle = _hdr(hdr_color)
    for col_i in range(1, len(columns) + 1):
        _apply(ws.cell(1, col_i), hstyle)
    ws.row_dimensions[1].height = 22

    for row_i, row in enumerate(rows, 2):
        ws.append(row)
        if row_i % 2 == 0:
            fill = PatternFill("solid", start_color=GRIS_FILA, end_color=GRIS_FILA)
            for col_i in range(1, len(columns) + 1):
                ws.cell(row_i, col_i).fill = fill

    if freeze:
        ws.freeze_panes = "A2"
    _autofit(ws)


def _safe_str(v):
    if isinstance(v, (bytes, bytearray)):
        return "[Archivo Binario]"
    if v is None:
        return ""
    return str(v)


def _query(conn, sql, params=None):
    with conn.cursor(pymysql.cursors.DictCursor) as cur:
        cur.execute(sql, params or ())
        return cur.fetchall()


# ── Hoja 1: Resumen KPIs ──────────────────────────────────────────────────────
def _sheet_resumen(wb, conn):
    ws = wb.create_sheet("Resumen_KPIs")
    ws.column_dimensions["A"].width = 32
    ws.column_dimensions["B"].width = 18

    titulo = ws.cell(1, 1, "REPORTE MAESTRO — CARRIER TRANSICOLD")
    titulo.font = Font(name="Arial", size=14, bold=True, color="FFFFFF")
    titulo.fill = PatternFill("solid", start_color=AZUL_CORP, end_color=AZUL_CORP)
    titulo.alignment = Alignment(horizontal="center", vertical="center")
    ws.merge_cells("A1:B1")
    ws.row_dimensions[1].height = 28

    fecha = ws.cell(2, 1, f"Generado: {datetime.now(TZ).strftime('%d/%m/%Y %H:%M')}")
    fecha.font = Font(name="Arial", size=9, italic=True, color="595959")
    ws.merge_cells("A2:B2")

    ws.append([])

    kpis = []
    try:
        kpis.append(("Unidades Registradas",   _query(conn, "SELECT COUNT(*) c FROM unidades")[0]["c"]))
        kpis.append(("Tickets Abiertos",        _query(conn, "SELECT COUNT(*) c FROM tickets WHERE atendido=0")[0]["c"]))
        kpis.append(("Tickets Cerrados",        _query(conn, "SELECT COUNT(*) c FROM tickets WHERE atendido=1")[0]["c"]))
        kpis.append(("Asignaciones Totales",    _query(conn, "SELECT COUNT(*) c FROM asignaciones")[0]["c"]))
        kpis.append(("Técnicos Activos",        _query(conn, "SELECT COUNT(*) c FROM users WHERE role != 'inactivo'")[0]["c"]))
        kpis.append(("Registros Asistencia",    _query(conn, "SELECT COUNT(*) c FROM registros_asistencia")[0]["c"]))
        kpis.append(("Horarios Configurados",   _query(conn, "SELECT COUNT(*) c FROM horarios")[0]["c"]))
    except Exception:
        pass

    label_style = Font(name="Arial", size=10, bold=True)
    val_style   = Font(name="Arial", size=11, bold=True, color="1F4E78")

    for row_i, (label, val) in enumerate(kpis, 4):
        ws.cell(row_i, 1, label).font = label_style
        c = ws.cell(row_i, 2, val)
        c.font = val_style
        c.alignment = Alignment(horizontal="center")
        if row_i % 2 == 0:
            for col_i in (1, 2):
                ws.cell(row_i, col_i).fill = PatternFill("solid", start_color=GRIS_FILA, end_color=GRIS_FILA)


# ── Hoja 2: Series / Unidades ─────────────────────────────────────────────────
def _sheet_unidades(wb, conn):
    ws = wb.create_sheet("Series_Unidades")
    rows_db = _query(conn, "SELECT * FROM unidades ORDER BY unit_number")
    if not rows_db:
        ws.cell(1, 1, "Sin registros").font = Font(italic=True)
        return
    cols = list(rows_db[0].keys())
    _write_sheet(ws, cols, [[_safe_str(r[c]) for c in cols] for r in rows_db])


# ── Hoja 3: Actividades ───────────────────────────────────────────────────────
def _sheet_actividades(wb, conn):
    ws = wb.create_sheet("Actividades")
    rows_db = _query(conn, """
        SELECT a.id, a.unidad, a.actividad_id, a.tecnico, a.estado,
               a.comentario, a.fecha_asignacion, a.fecha_inicio, a.fecha_fin, a.ticket_id
        FROM asignaciones a ORDER BY a.fecha_asignacion DESC
    """)
    if not rows_db:
        ws.cell(1, 1, "Sin registros").font = Font(italic=True)
        return
    cols = list(rows_db[0].keys())
    _write_sheet(ws, cols, [[_safe_str(r[c]) for c in cols] for r in rows_db])


# ── Hoja 4: Tickets ───────────────────────────────────────────────────────────
def _sheet_tickets(wb, conn):
    ws = wb.create_sheet("Tickets")
    rows_db = _query(conn, """
        SELECT t.ticket_num AS `Ticket #`,
               t.unit_number AS Unidad,
               u.vin_number AS VIN,
               t.descripcion AS `Descripción / Problema`,
               t.creado_por AS `Creado Por`,
               a.tecnico AS `Técnico Asignado`,
               t.atendido AS Atendido,
               t.reporte_enviado AS `Reporte Enviado`,
               COALESCE(t.reporte_texto, '—') AS `Reporte Final del Técnico`,
               t.fecha_atencion AS `Fecha Atención`,
               t.fecha_reporte AS `Fecha Reporte`
        FROM tickets t
        LEFT JOIN unidades u ON u.unit_number = t.unit_number
        LEFT JOIN asignaciones a ON a.ticket_id = t.id
        ORDER BY t.ticket_num DESC
    """)
    if not rows_db:
        ws.cell(1, 1, "Sin registros").font = Font(italic=True)
        return
    cols = list(rows_db[0].keys())
    _write_sheet(ws, cols, [[_safe_str(r[c]) for c in cols] for r in rows_db])


# ── Hoja 6: Horarios Semanales ────────────────────────────────────────────────
def _sheet_horarios(wb, conn):
    ws = wb.create_sheet("Horarios_Semanales")

    # Pivot: técnico × día
    rows_db = _query(conn, """
        SELECT username, fecha, semana, hora_entrada, hora_salida
        FROM horarios
        ORDER BY username, fecha
    """)

    cols = ["Técnico (username)", "Nombre Completo",
            "Lunes Entrada",  "Lunes Salida",
            "Martes Entrada", "Martes Salida",
            "Miércoles Entrada", "Miércoles Salida",
            "Jueves Entrada", "Jueves Salida",
            "Viernes Entrada","Viernes Salida",
            "Sábado Entrada", "Sábado Salida"]

    _write_sheet(ws, cols, [], hdr_color=VERDE)

    # Obtener nombres completos de users si hay columna nombre
    try:
        users_db = _query(conn, "SELECT username, username AS nombre FROM users")
        # try nombre_completo column
        try:
            users_db = _query(conn, "SELECT username, nombre_completo AS nombre FROM users")
        except Exception:
            pass
        nombres = {u["username"]: u["nombre"] for u in (users_db or [])}
    except Exception:
        nombres = {}

    # Agrupar por técnico
    from collections import defaultdict
    import datetime as _dt

    tec_data = defaultdict(dict)  # {username: {weekday_name: {entrada, salida}}}
    DAYS = {0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves", 4: "Viernes", 5: "Sábado"}

    for r in (rows_db or []):
        try:
            if hasattr(r["fecha"], "weekday"):
                wd = r["fecha"].weekday()
            else:
                wd = _dt.date.fromisoformat(str(r["fecha"])).weekday()
            day_name = DAYS.get(wd)
            if day_name:
                def _fmt_time(t):
                    if t is None:
                        return ""
                    if hasattr(t, "seconds"):  # timedelta
                        h, rem = divmod(t.seconds, 3600)
                        return f"{h:02d}:{rem//60:02d}"
                    return str(t)[:5]
                tec_data[r["username"]][day_name + " Entrada"] = _fmt_time(r["hora_entrada"])
                tec_data[r["username"]][day_name + " Salida"]  = _fmt_time(r["hora_salida"])
        except Exception:
            continue

    row_i = 2
    for tec, days in sorted(tec_data.items()):
        row = [
            tec,
            nombres.get(tec, tec),
            days.get("Lunes Entrada", ""),    days.get("Lunes Salida", ""),
            days.get("Martes Entrada", ""),   days.get("Martes Salida", ""),
            days.get("Miércoles Entrada", ""),days.get("Miércoles Salida", ""),
            days.get("Jueves Entrada", ""),   days.get("Jueves Salida", ""),
            days.get("Viernes Entrada", ""),  days.get("Viernes Salida", ""),
            days.get("Sábado Entrada", ""),   days.get("Sábado Salida", ""),
        ]
        ws.append(row)
        if row_i % 2 == 0:
            for ci in range(1, len(cols) + 1):
                ws.cell(row_i, ci).fill = PatternFill("solid", start_color=GRIS_FILA, end_color=GRIS_FILA)
        row_i += 1

    ws.freeze_panes = "A2"
    _autofit(ws)


# ── Hoja 7: Asistencia y Retardos ─────────────────────────────────────────────
def _sheet_asistencia(wb, conn):
    ws = wb.create_sheet("Asistencia_Retardos")

    cols = ["Fecha", "Técnico", "Tipo", "Hora Checkin",
            "Horario Programado Entrada", "Horario Programado Salida",
            "Retardo (min)", "Distancia (m)", "Aprobado", "Estado"]

    _write_sheet(ws, cols, [], hdr_color=VERDE)

    # Registros reales
    regs = _query(conn, """
        SELECT r.fecha, r.username, r.tipo, r.hora_checkin,
               r.distancia_metros, r.aprobado,
               COALESCE(r.retardo_min, 0) AS retardo_min
        FROM registros_asistencia r
        ORDER BY r.fecha DESC, r.hora_checkin
    """) or []

    # Horarios programados index por (username, fecha)
    horarios_db = _query(conn, "SELECT username, fecha, hora_entrada, hora_salida FROM horarios") or []
    from collections import defaultdict
    import datetime as _dt

    def _fmt_t(t):
        if t is None: return ""
        if hasattr(t, "seconds"):
            h, rem = divmod(t.seconds, 3600)
            return f"{h:02d}:{rem//60:02d}"
        return str(t)[:5]

    hor_idx = {}
    for h in horarios_db:
        try:
            if hasattr(h["fecha"], "weekday"):
                wd = h["fecha"].weekday()
                fecha_str = h["fecha"].isoformat()
            else:
                d = _dt.date.fromisoformat(str(h["fecha"]))
                wd = d.weekday()
                fecha_str = str(h["fecha"])
            hor_idx[(h["username"], fecha_str)] = (
                _fmt_t(h["hora_entrada"]),
                _fmt_t(h["hora_salida"])
            )
        except Exception:
            continue

    fill_amarillo = PatternFill("solid", start_color="FFF2CC", end_color="FFF2CC")
    fill_rojo     = PatternFill("solid", start_color="FFDADA", end_color="FFDADA")
    fill_verde    = PatternFill("solid", start_color="E2EFDA", end_color="E2EFDA")

    row_i = 2
    for r in regs:
        try:
            fecha_str = r["fecha"].isoformat() if hasattr(r["fecha"], "isoformat") else str(r["fecha"])
        except Exception:
            fecha_str = str(r.get("fecha", ""))

        hora_checkin = str(r.get("hora_checkin", "") or "")[:5]
        retardo      = int(r.get("retardo_min") or 0)
        aprobado     = r.get("aprobado", 0)
        distancia    = r.get("distancia_metros", "")
        tipo         = r.get("tipo", "")

        hor_e, hor_s = hor_idx.get((r["username"], fecha_str), ("", ""))

        if not aprobado:
            estado = "❌ Fuera de geocerca"
        elif retardo >= 30:
            estado = f"⚠️ Retardo severo +{retardo}min"
        elif retardo > 0:
            estado = f"⏱ Retardo +{retardo}min"
        else:
            estado = "✅ A tiempo"

        row = [fecha_str, r["username"], tipo, hora_checkin,
               hor_e, hor_s,
               retardo if retardo else "",
               distancia, "Sí" if aprobado else "No", estado]
        ws.append(row)

        # Color de fila según estado
        if retardo >= 30:
            fill = fill_rojo
        elif retardo > 0:
            fill = fill_amarillo
        elif aprobado:
            fill = fill_verde
        else:
            fill = fill_rojo

        for ci in range(1, len(cols) + 1):
            ws.cell(row_i, ci).fill = fill

        row_i += 1

    ws.freeze_panes = "A2"
    _autofit(ws)


# ── Hoja 8: Resumen Retardos por Técnico ─────────────────────────────────────
def _sheet_resumen_retardos(wb, conn):
    ws = wb.create_sheet("Resumen_Retardos_Tecnico")

    cols = ["Técnico", "Total Entradas", "Entradas a Tiempo",
            "Con Retardo", "Retardo Promedio (min)", "Retardo Máx (min)",
            "Registros Fuera Geocerca", "Días con Asistencia"]

    _write_sheet(ws, cols, [], hdr_color=AZUL_CLARO)

    rows_db = _query(conn, """
        SELECT
            username,
            SUM(tipo = 'entrada') AS total_entradas,
            SUM(tipo = 'entrada' AND COALESCE(retardo_min,0) = 0) AS a_tiempo,
            SUM(tipo = 'entrada' AND COALESCE(retardo_min,0) > 0) AS con_retardo,
            ROUND(AVG(CASE WHEN tipo='entrada' THEN COALESCE(retardo_min,0) END), 1) AS retardo_prom,
            MAX(CASE WHEN tipo='entrada' THEN COALESCE(retardo_min,0) END) AS retardo_max,
            SUM(aprobado = 0) AS fuera_geocerca,
            COUNT(DISTINCT fecha) AS dias_asistencia
        FROM registros_asistencia
        GROUP BY username
        ORDER BY con_retardo DESC, username
    """) or []

    row_i = 2
    fill_warn = PatternFill("solid", start_color="FFF2CC", end_color="FFF2CC")

    for r in rows_db:
        con_ret = int(r.get("con_retardo") or 0)
        row = [
            r["username"],
            r.get("total_entradas", 0),
            r.get("a_tiempo", 0),
            con_ret,
            r.get("retardo_prom", 0),
            r.get("retardo_max", 0),
            r.get("fuera_geocerca", 0),
            r.get("dias_asistencia", 0),
        ]
        ws.append(row)
        if con_ret > 3:
            for ci in range(1, len(cols) + 1):
                ws.cell(row_i, ci).fill = fill_warn
        row_i += 1

    ws.freeze_panes = "A2"
    _autofit(ws)


# ── Hoja 9: Inventario ────────────────────────────────────────────────────────
def _sheet_inventario(wb, conn):
    ws = wb.create_sheet("Inventario")
    try:
        rows_db = _query(conn, "SELECT * FROM inventario_data ORDER BY id")
    except Exception:
        try:
            rows_db = _query(conn, "SELECT * FROM inventario ORDER BY id")
        except Exception:
            ws.cell(1, 1, "Tabla de inventario no encontrada").font = Font(italic=True)
            return
    if not rows_db:
        ws.cell(1, 1, "Sin registros").font = Font(italic=True)
        return
    cols = list(rows_db[0].keys())
    _write_sheet(ws, cols, [[_safe_str(r[c]) for c in cols] for r in rows_db])


# ── Hoja 10: Usuarios ─────────────────────────────────────────────────────────
def _sheet_usuarios(wb, conn):
    ws = wb.create_sheet("Usuarios")
    rows_db = _query(conn, """
        SELECT id, username, role,
               CASE WHEN role = 'inactivo' THEN 'No' ELSE 'Sí' END AS activo
        FROM users ORDER BY role, username
    """) or []
    cols = ["ID", "Username", "Rol", "Activo"]
    _write_sheet(ws, cols, [[_safe_str(r[c]) for c in list(r.keys())] for r in rows_db])


# ── Endpoint principal ────────────────────────────────────────────────────────
@router.get("/exportar-maestro")
def exportar_sistema_completo(current_user=Depends(verify_token)):
    """
    Exporta el sistema completo a Excel con formato profesional.
    Incluye: KPIs, Unidades, Actividades, Tickets, Cierre, Horarios, Asistencia, Retardos.
    """
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="No hay conexión con la base de datos")

    try:
        wb = Workbook()
        wb.remove(wb.active)   # eliminar hoja en blanco por defecto

        builders = [
            ("Resumen_KPIs",             _sheet_resumen),
            ("Series_Unidades",          _sheet_unidades),
            ("Actividades",              _sheet_actividades),
            ("Tickets",                  _sheet_tickets),
            ("Horarios_Semanales",       _sheet_horarios),
            ("Asistencia_Retardos",      _sheet_asistencia),
            ("Resumen_Retardos_Tecnico", _sheet_resumen_retardos),
            ("Inventario",               _sheet_inventario),
            ("Usuarios",                 _sheet_usuarios),
        ]

        for name, fn in builders:
            try:
                fn(wb, connection)
            except Exception as e:
                # Si una hoja falla, la añadimos con nota de error en lugar de abortar todo
                ws = wb.create_sheet(name)
                ws.cell(1, 1, f"Error al generar esta hoja: {e}").font = Font(italic=True, color="FF0000")
                print(f"[reporte] Hoja '{name}' falló: {e}")

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)

        fecha_hoy = datetime.now(TZ).strftime("%Y%m%d_%H%M")
        filename  = f"Reporte_Maestro_CarrierTransicold_{fecha_hoy}.xlsx"

        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except Exception as e:
        print(f"Error al generar reporte maestro: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

    finally:
        connection.close()
