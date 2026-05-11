from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from db import execute_read
from auth import verify_token
import io

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
    total_u = len(execute_read("SELECT id FROM unidades"))
    estados = execute_read("SELECT estado FROM asignaciones")
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

# ── STATS POR TÉCNICO ──────────────────────────────────────────────────────
@router.get("/stats_tecnicos")
def get_stats_tecnicos(current_user: dict = Depends(verify_token)):
    return execute_read("""
        SELECT tecnico,
               COUNT(*) as total,
               SUM(estado='completada') as completadas,
               SUM(estado='en_proceso') as en_curso,
               SUM(estado='pendiente') as pendientes,
               ROUND(SUM(estado='completada') / COUNT(*) * 100) as rendimiento_pct
        FROM asignaciones
        GROUP BY tecnico
        ORDER BY completadas DESC
    """)

# ── ESTATUS POR UNIDAD (tabla de progreso) ─────────────────────────────────
@router.get("/estatus_unidades")
def get_estatus_unidades(current_user: dict = Depends(verify_token)):
    completadas = execute_read("SELECT unidad, actividad_id FROM asignaciones WHERE estado='completada'")
    completed_set = set((c["unidad"], c["actividad_id"]) for c in completadas)
    unidades = execute_read("SELECT unit_number, id_lote FROM unidades ORDER BY id_lote, unit_number")
    resultado = []
    for u in unidades:
        row = {"LOTE": u["id_lote"], "#Económico": u["unit_number"]}
        for act in ACTIVIDADES_CARRIER:
            row[act] = "✔" if (u["unit_number"], act) in completed_set else "–"
        resultado.append(row)
    return resultado

# ── DESCARGAR REPORTE EXCEL ────────────────────────────────────────────────
@router.get("/reporte-excel")
def reporte_excel(current_user: dict = Depends(verify_token)):
    try:
        import openpyxl
        from openpyxl.styles import PatternFill, Font, Alignment
    except ImportError:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="openpyxl no instalado. Agrega 'openpyxl' a requirements.txt")

    wb = openpyxl.Workbook()

    # Hoja 1: Unidades y series
    ws1 = wb.active
    ws1.title = "Series_Unidades"
    unidades = execute_read("SELECT * FROM unidades ORDER BY id_lote, unit_number")
    if unidades:
        headers = list(unidades[0].keys())
        ws1.append(headers)
        for u in unidades:
            ws1.append(list(u.values()))

    # Hoja 2: Actividades
    ws2 = wb.create_sheet("Actividades")
    asigs = execute_read("SELECT * FROM asignaciones ORDER BY id DESC")
    if asigs:
        headers2 = list(asigs[0].keys())
        ws2.append(headers2)
        for a in asigs:
            ws2.append(list(a.values()))

    # Hoja 3: Tickets
    ws3 = wb.create_sheet("Tickets")
    tickets = execute_read("SELECT * FROM tickets ORDER BY ticket_num DESC")
    if tickets:
        headers3 = list(tickets[0].keys())
        ws3.append(headers3)
        for t in tickets:
            ws3.append(list(t.values()))

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    from datetime import datetime
    fecha = datetime.now().strftime("%Y-%m-%d")
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=Carrier_Reporte_{fecha}.xlsx"}
    )
