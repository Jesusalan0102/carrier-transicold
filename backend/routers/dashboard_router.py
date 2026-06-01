from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from db import execute_read
from datetime import datetime

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)

@router.get("/kpis")
def obtener_kpis():
    """KPIs del Dashboard: total_unidades, completadas, en_proceso, pendientes, avance"""
    try:
        # Total de unidades registradas
        res_unidades = execute_read("SELECT COUNT(*) as total FROM unidades")
        total_unidades = res_unidades[0]['total'] if res_unidades else 0

        # Conteo de asignaciones por estado
        res_estados = execute_read(
            "SELECT estado, COUNT(*) as cantidad FROM asignaciones GROUP BY estado"
        ) or []
        estados = {row['estado']: row['cantidad'] for row in res_estados}

        completadas = estados.get('completada', 0)
        en_proceso  = estados.get('en_proceso', 0)
        pendientes  = estados.get('pendiente', 0)
        total_asig  = completadas + en_proceso + pendientes

        avance = round((completadas / total_asig * 100), 1) if total_asig > 0 else 0

        return {
            "status": "success",
            "total_unidades": total_unidades,
            "completadas": completadas,
            "en_proceso": en_proceso,
            "pendientes": pendientes,
            "avance": avance
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats_tecnicos")
def obtener_stats_tecnicos():
    """Estadísticas de carga de trabajo por técnico"""
    try:
        stats = execute_read(
            """
            SELECT
                tecnico,
                COUNT(*) as cantidad,
                SUM(CASE WHEN estado = 'completada' THEN 1 ELSE 0 END) as completadas,
                SUM(CASE WHEN estado = 'en_proceso' THEN 1 ELSE 0 END) as en_curso,
                SUM(CASE WHEN estado = 'pendiente'  THEN 1 ELSE 0 END) as pendientes
            FROM asignaciones
            WHERE tecnico IS NOT NULL AND tecnico != ''
            GROUP BY tecnico
            ORDER BY cantidad DESC
            """
        ) or []
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reporte-excel")
def reporte_excel():
    """Genera y descarga el Reporte Maestro en formato Excel (.xlsx)"""
    try:
        tickets = execute_read(
            "SELECT ticket_num, unit_number, vin_number, descripcion, creado_por, "
            "tecnico, atendido, reporte_enviado, fecha_creacion, "
            "fecha_atencion, fecha_reporte FROM tickets ORDER BY ticket_num DESC"
        ) or []

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Reporte Maestro"
        ws.views.sheetView[0].showGridLines = True

        headers = [
            "Núm. Ticket", "Número de Unidad", "Número VIN", "Descripción",
            "Creado Por", "Técnico Asignado", "Atendido (Sí/No)",
            "Reporte Enviado", "Fecha Creación", "Fecha Atención", "Fecha Reporte"
        ]

        header_font  = Font(name="Arial", size=11, bold=True, color="FFFFFF")
        header_fill  = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
        thin_border  = Border(
            left=Side(style='thin', color='D9D9D9'),
            right=Side(style='thin', color='D9D9D9'),
            top=Side(style='thin', color='D9D9D9'),
            bottom=Side(style='thin', color='D9D9D9')
        )

        ws.append(headers)
        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_num)
            cell.font      = header_font
            cell.fill      = header_fill
            cell.alignment = center_align
            cell.border    = thin_border

        for t in tickets:
            def fmt_date(val):
                if isinstance(val, datetime):
                    return val.strftime('%Y-%m-%d %H:%M:%S')
                return str(val) if val else ""

            ws.append([
                t.get("ticket_num"),
                t.get("unit_number"),
                t.get("vin_number"),
                t.get("descripcion"),
                t.get("creado_por"),
                t.get("tecnico"),
                "Sí" if t.get("atendido") else "No",
                "Enviado" if t.get("reporte_enviado") else "Pendiente",
                fmt_date(t.get("fecha_creacion")),
                fmt_date(t.get("fecha_atencion")),
                fmt_date(t.get("fecha_reporte")),
            ])

        for row in ws.iter_rows(min_row=2, max_row=len(tickets) + 1, min_col=1, max_col=len(headers)):
            for cell in row:
                cell.font   = Font(name="Arial", size=10)
                cell.border = thin_border
                if cell.column in [1, 7, 8, 9, 10, 11]:
                    cell.alignment = Alignment(horizontal="center")

        for col in ws.columns:
            max_len    = max(len(str(cell.value or '')) for cell in col)
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

        file_stream = io.BytesIO()
        wb.save(file_stream)
        file_stream.seek(0)

        return StreamingResponse(
            file_stream,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=reporte_maestro_tickets.xlsx"}
        )

    except Exception as e:
        print(f"Error crítico en reporte-excel: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno al generar excel: {str(e)}")
