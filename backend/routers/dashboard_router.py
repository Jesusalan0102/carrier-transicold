from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import io
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from db import execute_read  # Importación correcta desde db.py
from datetime import datetime

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)

@router.get("/kpis")
def obtener_kpis():
    """Ruta complementaria para KPIs del Dashboard"""
    try:
        total_tickets = execute_read("SELECT COUNT(*) as total FROM tickets")
        return {"status": "success", "total_tickets": total_tickets[0]['total'] if total_tickets else 0}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats_tecnicos")
def obtener_stats_tecnicos():
    """Ruta complementaria para estadísticas de técnicos"""
    try:
        stats = execute_read("SELECT tecnico, COUNT(*) as cantidad FROM tickets GROUP BY tecnico") or []
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reporte-excel")
def reporte_excel():
    """
    Genera y descarga el Reporte Maestro en formato Excel (.xlsx)
    CORREGIDO: Sin columnas inexistentes en DB.
    """
    try:
        # Consulta limpia de campos inválidos
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
        
        header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="1F4E78", end_color="1F4E78", fill_type="solid")
        center_alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        thin_border = Border(
            left=Side(style='thin', color='D9D9D9'),
            right=Side(style='thin', color='D9D9D9'),
            top=Side(style='thin', color='D9D9D9'),
            bottom=Side(style='thin', color='D9D9D9')
        )
        
        ws.append(headers)
        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=1, column=col_num)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = center_alignment
            cell.border = thin_border
            
        for t in tickets:
            row_data = [
                t.get("ticket_num"),
                t.get("unit_number"),
                t.get("vin_number"),
                t.get("descripcion"),
                t.get("creado_por"),
                t.get("tecnico"),
                "Sí" if t.get("atendido") else "No",
                "Enviado" if t.get("reporte_enviado") else "Pendiente",
                t.get("fecha_creacion").strftime('%Y-%m-%d %H:%M:%S') if isinstance(t.get("fecha_creacion"), datetime) else str(t.get("fecha_creacion") or ""),
                t.get("fecha_atencion").strftime('%Y-%m-%d %H:%M:%S') if isinstance(t.get("fecha_atencion"), datetime) else str(t.get("fecha_atencion") or ""),
                t.get("fecha_reporte").strftime('%Y-%m-%d %H:%M:%S') if isinstance(t.get("fecha_reporte"), datetime) else str(t.get("fecha_reporte") or "")
            ]
            ws.append(row_data)
            
        for row in ws.iter_rows(min_row=2, max_row=len(tickets) + 1, min_col=1, max_col=len(headers)):
            for cell in row:
                cell.font = Font(name="Arial", size=10)
                cell.border = thin_border
                if cell.column in [1, 7, 8, 9, 10, 11]:
                    cell.alignment = Alignment(horizontal="center")
                    
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
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
