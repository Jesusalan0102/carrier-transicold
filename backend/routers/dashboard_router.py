from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from db import execute_read
from auth import verify_token
from datetime import datetime
from zoneinfo import ZoneInfo
import io
import logging

TZ = ZoneInfo("America/Tijuana")

# ── Importación opcional de OneDrive ────────────────────────────────────────
try:
    from onedrive_service import sync_reporte_maestro
    ONEDRIVE_ENABLED = True
except ImportError:
    ONEDRIVE_ENABLED = False

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

ACTIVIDADES_CARRIER = [
    "Cableado","Programación","Soldadura","Check de fugas",
    "Vacío","Cerrado","Pre-viaje","Horas Corridas",
    "Standby","GPS","Corriendo","Inspección",
    "Accesorios","Toma de Valores","Evidencia","Toma de Series",
]

# ── KPIs PRINCIPALES ───────────────────────────────────────────────────────
@router.get("/kpis")
def get_kpis(current_user: dict = Depends(verify_token)):
    total_u = len(execute_read("SELECT id FROM unidades WHERE oculto=0"))
    unidades_visibles = execute_read("SELECT unit_number FROM unidades WHERE oculto=0")
    visibles_set = set(u["unit_number"] for u in unidades_visibles)
    estados_rows = execute_read("SELECT estado, unidad FROM asignaciones")
    estados = [e for e in estados_rows if e["unidad"] in visibles_set]
    completadas = sum(1 for e in estados if e["estado"] == "completada")
    en_proceso  = sum(1 for e in estados if e["estado"] == "en_proceso")
    pendientes  = sum(1 for e in estados if e["estado"] == "pendiente")
    total_t = len(estados)
    avance = round(completadas / total_t * 100) if total_t else 0
    tickets_sin_atender = len(execute_read("SELECT id FROM tickets WHERE atendido=FALSE"))
    solicitudes_pendientes = len(execute_read("SELECT id FROM asignaciones WHERE estado='solicitado'"))
    return {
        "total_unidades": total_u,
        "completadas": completadas,
        "en_proceso": en_proceso,
        "pendientes": pendientes,
        "avance": avance,
        "tickets_sin_atender": tickets_sin_atender,
        "solicitudes_pendientes": solicitudes_pendientes,
    }

# ── STATS POR TÉCNICO (excluye lotes ocultos) ─────────────────────────────
@router.get("/stats_tecnicos")
def get_stats_tecnicos(current_user: dict = Depends(verify_token)):
    return execute_read("""
        SELECT a.tecnico,
               COUNT(*) as total,
               SUM(a.estado='completada') as completadas,
               SUM(a.estado='en_proceso') as en_curso,
               SUM(a.estado='pendiente') as pendientes,
               ROUND(SUM(a.estado='completada') / COUNT(*) * 100) as rendimiento_pct
        FROM asignaciones a
        INNER JOIN unidades u ON u.unit_number = a.unidad
        WHERE u.oculto = 0
        GROUP BY a.tecnico
        ORDER BY completadas DESC
    """)

# ── DISTRIBUCIÓN GLOBAL DE ESTADOS (excluye lotes ocultos) ────────────────
@router.get("/distribucion_global")
def get_distribucion_global(current_user: dict = Depends(verify_token)):
    rows = execute_read("""
        SELECT a.estado, COUNT(*) as total
        FROM asignaciones a
        INNER JOIN unidades u ON u.unit_number = a.unidad
        WHERE u.oculto = 0
        GROUP BY a.estado
    """)
    cnt = {"completada": 0, "en_proceso": 0, "pendiente": 0}
    for r in rows:
        if r["estado"] in cnt:
            cnt[r["estado"]] = r["total"]
    return cnt

# ── ESTATUS POR UNIDAD ─────────────────────────────────────────────────────
@router.get("/estatus_unidades")
def get_estatus_unidades(current_user: dict = Depends(verify_token)):
    completadas = execute_read("SELECT unidad, actividad_id FROM asignaciones WHERE estado='completada'")
    completed_set = set((c["unidad"], c["actividad_id"]) for c in completadas)
    unidades = execute_read("SELECT unit_number, id_lote FROM unidades WHERE oculto=0 ORDER BY id_lote, unit_number")
    resultado = []
    for u in unidades:
        row = {"LOTE": u["id_lote"], "#Económico": u["unit_number"]}
        for act in ACTIVIDADES_CARRIER:
            row[act] = "✔" if (u["unit_number"], act) in completed_set else "–"
        resultado.append(row)
    return resultado

# ── DESCARGAR REPORTE EXCEL (+ auto-sync a OneDrive) ──────────────────────
@router.get("/reporte-excel")
def reporte_excel(current_user: dict = Depends(verify_token)):
    try:
        import openpyxl
        from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
    except ImportError:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="openpyxl no instalado. Agrega 'openpyxl' a requirements.txt")

    wb = openpyxl.Workbook()

    # ── Estilos globales ───────────────────────────────────────────────────
    THIN   = Side(style='thin', color="BFBFBF")
    BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
    HDR_FILL  = PatternFill("solid", start_color="1F4E79")
    HDR_FONT  = Font(bold=True, color="FFFFFF", name="Arial", size=10)
    HDR_ALIGN = Alignment(horizontal="center", vertical="center", wrap_text=True)
    BODY_FONT = Font(name="Arial", size=9)
    BODY_ALIGN= Alignment(vertical="center", wrap_text=True)

    def write_sheet(ws, rows, col_widths: dict = None):
        if not rows:
            ws.append(["Sin datos"])
            return
        headers = list(rows[0].keys())
        for col_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col_idx, value=h)
            cell.fill = HDR_FILL
            cell.font = HDR_FONT
            cell.alignment = HDR_ALIGN
            cell.border = BORDER
        for row_idx, row in enumerate(rows, 2):
            for col_idx, val in enumerate(row.values(), 1):
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                cell.font = BODY_FONT
                cell.alignment = BODY_ALIGN
                cell.border = BORDER
        for col_idx, h in enumerate(headers, 1):
            width = (col_widths or {}).get(h, min(len(str(h)) + 6, 35))
            ws.column_dimensions[get_column_letter(col_idx)].width = width
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

    def colorear_estado(ws, rows, col_name):
        if not rows:
            return
        headers = list(rows[0].keys())
        if col_name not in headers:
            return
        col_idx = headers.index(col_name) + 1
        COLOR_MAP = {
            "completada": ("C6EFCE", "276221"),
            "en_proceso": ("DDEBF7", "1F4E79"),
            "pendiente":  ("FFEB9C", "7D6608"),
            "solicitado": ("FFEB9C", "7D6608"),
        }
        for row_idx in range(2, len(rows) + 2):
            cell = ws.cell(row=row_idx, column=col_idx)
            colors = COLOR_MAP.get(str(cell.value or "").lower())
            if colors:
                cell.fill = PatternFill("solid", start_color=colors[0])
                cell.font = Font(name="Arial", size=9, color=colors[1], bold=True)

    def colorear_semaforo_tickets(ws, rows):
        if not rows:
            return
        headers = list(rows[0].keys())
        n_cols = len(headers)
        atendido_idx  = headers.index("Atendido")        + 1 if "Atendido"        in headers else None
        reporte_idx   = headers.index("Reporte Enviado") + 1 if "Reporte Enviado" in headers else None
        ROJO     = PatternFill("solid", start_color="FFCCCC")
        AMARILLO = PatternFill("solid", start_color="FFFACD")
        VERDE    = PatternFill("solid", start_color="C6EFCE")
        for row_idx, row in enumerate(rows, 2):
            vals = list(row.values())
            atendido    = bool(vals[atendido_idx - 1])  if atendido_idx else False
            reporte_env = bool(vals[reporte_idx - 1])   if reporte_idx  else False
            fill = VERDE if reporte_env else (AMARILLO if atendido else ROJO)
            for col_idx in range(1, n_cols + 1):
                ws.cell(row=row_idx, column=col_idx).fill = fill

    # ── Hoja 1: Resumen KPIs ───────────────────────────────────────────────
    ws_kpi = wb.active
    ws_kpi.title = "Resumen_KPIs"

    total_u_rows = execute_read("SELECT id FROM unidades")
    estados_rows = execute_read("SELECT estado FROM asignaciones")
    comp  = sum(1 for e in estados_rows if e["estado"] == "completada")
    proc  = sum(1 for e in estados_rows if e["estado"] == "en_proceso")
    pend  = sum(1 for e in estados_rows if e["estado"] == "pendiente")
    total = len(estados_rows)
    avance_pct = round(comp / total * 100, 1) if total else 0
    tkt_rows = execute_read("SELECT atendido, reporte_enviado FROM tickets")
    tkt_total     = len(tkt_rows)
    tkt_atendidos = sum(1 for t in tkt_rows if t["atendido"])
    tkt_reporte   = sum(1 for t in tkt_rows if t["reporte_enviado"])

    TITLE_FONT  = Font(bold=True, color="FFFFFF", name="Arial", size=13)
    KPI_LABEL   = Font(bold=True, name="Arial", size=10)
    KPI_VAL     = Font(name="Arial", size=12, bold=True, color="1F4E79")
    KPI_ALIGN_R = Alignment(horizontal="right", vertical="center")
    KPI_ALIGN_C = Alignment(horizontal="center", vertical="center")

    ws_kpi.merge_cells("B2:D2")
    ws_kpi["B2"] = "REPORTE MAESTRO — RESUMEN EJECUTIVO"
    ws_kpi["B2"].fill = HDR_FILL
    ws_kpi["B2"].font = TITLE_FONT
    ws_kpi["B2"].alignment = Alignment(horizontal="center", vertical="center")
    ws_kpi.row_dimensions[2].height = 30

    kpis = [
        ("Unidades Registradas",        len(total_u_rows)),
        ("Actividades Completadas",     comp),
        ("Actividades En Proceso",      proc),
        ("Actividades Pendientes",      pend),
        ("% Avance General",            f"{avance_pct}%"),
        ("Tickets Totales",             tkt_total),
        ("Tickets Atendidos",           tkt_atendidos),
        ("Reportes de Cierre Enviados", tkt_reporte),
    ]
    for i, (label, val) in enumerate(kpis, 4):
        ws_kpi[f"B{i}"] = label
        ws_kpi[f"B{i}"].font = KPI_LABEL
        ws_kpi[f"B{i}"].alignment = KPI_ALIGN_R
        ws_kpi[f"B{i}"].border = BORDER
        ws_kpi[f"C{i}"] = val
        ws_kpi[f"C{i}"].font = KPI_VAL
        ws_kpi[f"C{i}"].alignment = KPI_ALIGN_C
        ws_kpi[f"C{i}"].border = BORDER
    ws_kpi.column_dimensions["B"].width = 34
    ws_kpi.column_dimensions["C"].width = 18

    # ── Hoja 2: Series Unidades ────────────────────────────────────────────
    ws1 = wb.create_sheet("Series_Unidades")
    unidades = execute_read("SELECT * FROM unidades ORDER BY id_lote, unit_number")
    write_sheet(ws1, unidades, col_widths={
        "unit_number": 14, "id_lote": 14, "vin_number": 20,
        "engine_serial": 20, "compressor_serial": 22,
        "reefer_serial": 20, "reefer_model": 18,
        "evaporator_serial_mjs11": 24, "evaporator_serial_mjd22": 24,
        "generator_serial": 20, "battery_charger_serial": 22,
    })

    # ── Hoja 3: Actividades ────────────────────────────────────────────────
    ws2 = wb.create_sheet("Actividades")
    asigs = execute_read("""
        SELECT a.id, a.unidad, a.actividad_id, a.tecnico, a.estado,
               COALESCE(c.comentarios, a.comentario) AS comentario,
               a.fecha_asignacion, a.fecha_inicio, a.fecha_fin, a.ticket_id
        FROM asignaciones a
        LEFT JOIN (
            SELECT asignacion_id,
                   GROUP_CONCAT(
                       CONCAT(tecnico, ' (', DATE_FORMAT(fecha, '%%d/%%m/%%Y %%H:%%i'), '): ', comentario)
                       ORDER BY fecha SEPARATOR '  |  '
                   ) AS comentarios
            FROM comentarios_actividades
            GROUP BY asignacion_id
        ) c ON c.asignacion_id = a.id
        ORDER BY a.id DESC
    """)
    write_sheet(ws2, asigs, col_widths={
        "actividad_id": 22, "tecnico": 18, "estado": 14,
        "comentario": 50, "fecha_asignacion": 20,
        "fecha_inicio": 20, "fecha_fin": 20,
    })
    colorear_estado(ws2, asigs, "estado")

    # ── Hoja 4: Tickets ────────────────────────────────────────────────────
    ws3 = wb.create_sheet("Tickets")
    tickets = execute_read("""
        SELECT
            ticket_num          AS `Ticket #`,
            unit_number         AS `Unidad`,
            vin_number          AS `VIN`,
            descripcion         AS `Problema Reportado`,
            creado_por          AS `Creado Por`,
            tecnico             AS `Técnico Asignado`,
            atendido            AS `Atendido`,
            reporte_enviado     AS `Reporte Enviado`,
            COALESCE(reporte_texto, '—') AS `Reporte Final del Técnico`,
            fecha_creacion      AS `Fecha Creación`,
            fecha_atencion      AS `Fecha Atención`,
            fecha_reporte       AS `Fecha Reporte`
        FROM tickets
        ORDER BY ticket_num DESC
    """)
    write_sheet(ws3, tickets, col_widths={
        "Ticket #": 10, "Unidad": 14, "VIN": 20,
        "Problema Reportado": 35, "Creado Por": 18,
        "Técnico Asignado": 20, "Atendido": 12,
        "Reporte Enviado": 16,
        "Reporte Final del Técnico": 60,
        "Fecha Creación": 20, "Fecha Atención": 20, "Fecha Reporte": 20,
    })
    colorear_semaforo_tickets(ws3, tickets)

    # ── Hoja 5: Reporte Cierre ─────────────────────────────────────────────
    ws4 = wb.create_sheet("Reporte_Cierre_Tickets")
    cierre = execute_read("""
        SELECT
            t.ticket_num                        AS `Ticket #`,
            t.unit_number                       AS `Unidad`,
            t.vin_number                        AS `VIN`,
            t.descripcion                       AS `Problema Reportado`,
            t.creado_por                        AS `Creado Por`,
            t.tecnico                           AS `Técnico Asignado`,
            t.fecha_creacion                    AS `Fecha Creación`,
            t.fecha_atencion                    AS `Fecha Atención`,
            a.actividad_id                      AS `Actividad`,
            a.estado                            AS `Estado Actividad`,
            a.fecha_inicio                      AS `Inicio Trabajo`,
            a.fecha_fin                         AS `Fin Trabajo`,
            a.comentario                        AS `Comentario Técnico`,
            COALESCE(t.reporte_texto, '—')      AS `Reporte Final del Técnico`,
            t.fecha_reporte                     AS `Fecha Reporte Final`,
            t.reporte_enviado                   AS `Ticket Cerrado`
        FROM tickets t
        LEFT JOIN asignaciones a ON a.ticket_id = t.id
        ORDER BY t.ticket_num DESC
    """)
    write_sheet(ws4, cierre, col_widths={
        "Ticket #": 10, "Unidad": 12, "VIN": 20,
        "Problema Reportado": 35, "Creado Por": 18,
        "Técnico Asignado": 20, "Fecha Creación": 20,
        "Fecha Atención": 20, "Actividad": 22,
        "Estado Actividad": 16, "Inicio Trabajo": 20,
        "Fin Trabajo": 20, "Comentario Técnico": 45,
        "Reporte Final del Técnico": 60,
        "Fecha Reporte Final": 22, "Ticket Cerrado": 15,
    })
    colorear_estado(ws4, cierre, "Estado Actividad")

    if cierre:
        headers_cierre = list(cierre[0].keys())
        if "Reporte Final del Técnico" in headers_cierre:
            col_rf = headers_cierre.index("Reporte Final del Técnico") + 1
            RF_FILL = PatternFill("solid", start_color="EEF4FB")
            RF_FONT = Font(name="Arial", size=9, color="1F4E79", italic=True)
            for row_idx in range(2, len(cierre) + 2):
                cell = ws4.cell(row=row_idx, column=col_rf)
                cell.fill = RF_FILL
                cell.font = RF_FONT
                cell.alignment = Alignment(vertical="center", wrap_text=True)

    # ── Generar bytes del Excel ────────────────────────────────────────────
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    excel_bytes = buf.getvalue()

    fecha = datetime.now(TZ).strftime("%Y-%m-%d")

    # ── Auto-sync a OneDrive cada vez que se descarga el reporte ──────────
    if ONEDRIVE_ENABLED:
        try:
            web_url = sync_reporte_maestro(excel_bytes, fecha)
            logger.info(f"[OneDrive] Reporte guardado: {web_url}")
        except Exception as e:
            # No bloquear la descarga si OneDrive falla
            logger.warning(f"[OneDrive] No se pudo sincronizar reporte: {e}")

    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=Carrier_Reporte_{fecha}.xlsx"}
    )
