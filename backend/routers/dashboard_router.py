from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from db import execute_read
from auth import verify_token
import io

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


# ── KPIs ───────────────────────────────────────────────────────────────────────
@router.get("/kpis")
def get_kpis(current_user=Depends(verify_token)):
    try:
        total_unidades = execute_read("SELECT COUNT(*) as total FROM unidades")[0]["total"]
        total_acts     = execute_read("SELECT COUNT(*) as total FROM asignaciones")[0]["total"]
        completadas    = execute_read("SELECT COUNT(*) as total FROM asignaciones WHERE estado='completada'")[0]["total"]
        en_proceso     = execute_read("SELECT COUNT(*) as total FROM asignaciones WHERE estado='en_proceso'")[0]["total"]
        pendientes     = execute_read("SELECT COUNT(*) as total FROM asignaciones WHERE estado='pendiente'")[0]["total"]
        # Avance = % de actividades completadas sobre total de actividades
        avance = round((completadas / total_acts * 100), 1) if total_acts > 0 else 0
        return {
            "total_unidades": total_unidades,
            "completadas":    completadas,
            "en_proceso":     en_proceso,
            "pendientes":     pendientes,
            "avance":         avance,
            "total_usuarios":               execute_read("SELECT COUNT(*) as total FROM users")[0]["total"],
            "total_asignaciones":           total_acts,
            "asignaciones_completadas_mes": completadas,
            "porcentaje_actividad":         avance,
        }
    except Exception as e:
        print(f"Error en kpis: {e}")
        return {"total_unidades":0,"completadas":0,"en_proceso":0,"pendientes":0,"avance":0,
                "total_usuarios":0,"total_asignaciones":0,"asignaciones_completadas_mes":0,"porcentaje_actividad":0}


# ── Stats técnicos ─────────────────────────────────────────────────────────────
@router.get("/stats_tecnicos")
def get_stats_tecnicos(current_user=Depends(verify_token)):
    try:
        tecnicos = execute_read("SELECT id, username FROM users WHERE role='tecnico'")
        resultado = []
        for t in tecnicos:
            uname = t["username"]
            completadas = execute_read("SELECT COUNT(*) as total FROM asignaciones WHERE tecnico=%s AND estado='completada'", (uname,))[0]["total"]
            en_curso    = execute_read("SELECT COUNT(*) as total FROM asignaciones WHERE tecnico=%s AND estado='en_proceso'",  (uname,))[0]["total"]
            pendientes  = execute_read("SELECT COUNT(*) as total FROM asignaciones WHERE tecnico=%s AND estado='pendiente'",   (uname,))[0]["total"]
            resultado.append({"id":t["id"],"nombre":uname,"tecnico":uname,
                "completadas":completadas,"en_curso":en_curso,"pendientes":pendientes,
                "total_asignaciones":completadas+en_curso+pendientes,"asistencias_30dias":0,"activo":True})
        return resultado
    except Exception as e:
        print(f"Error en stats_tecnicos: {e}")
        return []


# ── Reporte Excel completo (5 hojas) ──────────────────────────────────────────
@router.get("/reporte-excel")
def reporte_excel(current_user=Depends(verify_token)):
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        from datetime import datetime

        wb = openpyxl.Workbook()
        AZUL    = PatternFill("solid", fgColor="002B5B")
        VERDE   = PatternFill("solid", fgColor="16a34a")
        AMARILLO= PatternFill("solid", fgColor="d97706")
        ROJO    = PatternFill("solid", fgColor="dc2626")
        GRIS    = PatternFill("solid", fgColor="F3F4F6")
        HDR     = Font(color="FFFFFF", bold=True, size=11)
        CENTER  = Alignment(horizontal="center", vertical="center", wrap_text=True)
        LEFT    = Alignment(horizontal="left",   vertical="center", wrap_text=True)

        def hdr(ws, row, cols):
            for c, v in enumerate(cols, 1):
                cell = ws.cell(row=row, column=c, value=v)
                cell.fill = AZUL; cell.font = HDR; cell.alignment = CENTER

        def widths(ws):
            for col in ws.columns:
                w = max((len(str(c.value or "")) for c in col), default=10)
                ws.column_dimensions[col[0].column_letter].width = min(max(w+2, 10), 45)

        # ── Hoja 1: Resumen KPIs ──────────────────────────────────────────────
        ws1 = wb.active; ws1.title = "Resumen_KPIs"
        ws1.merge_cells("B2:D2")
        ws1["B2"].value = "REPORTE MAESTRO — RESUMEN EJECUTIVO"
        ws1["B2"].font  = Font(color="002B5B", bold=True, size=14)
        ws1["B2"].alignment = CENTER

        total_unidades = execute_read("SELECT COUNT(*) as t FROM unidades")[0]["t"]
        total_acts     = execute_read("SELECT COUNT(*) as t FROM asignaciones")[0]["t"]
        completadas    = execute_read("SELECT COUNT(*) as t FROM asignaciones WHERE estado='completada'")[0]["t"]
        en_proceso     = execute_read("SELECT COUNT(*) as t FROM asignaciones WHERE estado='en_proceso'")[0]["t"]
        pendientes_k   = execute_read("SELECT COUNT(*) as t FROM asignaciones WHERE estado='pendiente'")[0]["t"]
        avance         = round(completadas/total_acts*100,1) if total_acts>0 else 0
        total_tickets  = execute_read("SELECT COUNT(*) as t FROM tickets")[0]["t"]
        t_abiertos     = execute_read("SELECT COUNT(*) as t FROM tickets WHERE atendido=0")[0]["t"]

        for i,(label,val) in enumerate([
            ("Unidades Registradas",    total_unidades),
            ("Actividades Completadas", completadas),
            ("Actividades En Proceso",  en_proceso),
            ("Actividades Pendientes",  pendientes_k),
            ("Avance Global (%)",       avance),
            ("Total Tickets",           total_tickets),
            ("Tickets Abiertos",        t_abiertos),
            ("Fecha del Reporte",       datetime.now().strftime("%Y-%m-%d %H:%M")),
        ], 4):
            ws1.cell(i,2,label).font = Font(bold=True, color="002B5B")
            ws1.cell(i,3,val)
        ws1.column_dimensions["B"].width = 30
        ws1.column_dimensions["C"].width = 20

        # ── Hoja 2: Series_Unidades ───────────────────────────────────────────
        ws2 = wb.create_sheet("Series_Unidades")
        c2 = ["id","unit_number","id_lote","vin_number","engine_serial","compressor_serial",
              "fecha_registro","reefer_serial","reefer_model","evaporator_serial_mjs11",
              "evaporator_serial_mjd22","generator_serial","battery_charger_serial"]
        hdr(ws2, 1, c2)
        unidades = execute_read(
            "SELECT id,unit_number,id_lote,vin_number,engine_serial,compressor_serial,"
            "fecha_registro,reefer_serial,reefer_model,evaporator_serial_mjs11,"
            "evaporator_serial_mjd22,generator_serial,battery_charger_serial "
            "FROM unidades ORDER BY id_lote,unit_number") or []
        for r,u in enumerate(unidades,2):
            for c,k in enumerate(c2,1):
                cell=ws2.cell(r,c,str(u.get(k) or "")); cell.alignment=LEFT
                if r%2==0: cell.fill=GRIS
        widths(ws2)

        # ── Hoja 3: Actividades ───────────────────────────────────────────────
        ws3 = wb.create_sheet("Actividades")
        c3 = ["id","unidad","actividad_id","tecnico","estado","comentario",
              "fecha_asignacion","fecha_inicio","fecha_fin","ticket_id"]
        hdr(ws3, 1, c3)
        asigs = execute_read(
            "SELECT id,unidad,actividad_id,tecnico,estado,comentario,"
            "fecha_asignacion,fecha_inicio,fecha_fin,ticket_id "
            "FROM asignaciones ORDER BY fecha_asignacion DESC") or []
        estado_fill = {"completada":VERDE,"en_proceso":AMARILLO,"pendiente":ROJO}
        for r,a in enumerate(asigs,2):
            fill = estado_fill.get(a.get("estado",""), GRIS if r%2==0 else PatternFill())
            for c,k in enumerate(c3,1):
                cell=ws3.cell(r,c,str(a.get(k) or "")); cell.alignment=LEFT; cell.fill=fill
        widths(ws3)

        # ── Hoja 4: Tickets ───────────────────────────────────────────────────
        ws4 = wb.create_sheet("Tickets")
        c4 = ["Ticket #","Unidad","VIN","Problema Reportado","Creado Por",
              "Técnico Asignado","Atendido","Reporte Enviado",
              "Reporte Final del Técnico","Fecha Creación","Fecha Atención","Fecha Reporte"]
        hdr(ws4, 1, c4)
        tickets = execute_read(
            "SELECT ticket_num,unit_number,vin_number,descripcion,creado_por,"
            "tecnico,atendido,reporte_enviado,reporte,fecha_creacion,"
            "fecha_atencion,fecha_reporte FROM tickets ORDER BY ticket_num DESC") or []
        for r,t in enumerate(tickets,2):
            vals=[t.get("ticket_num"),t.get("unit_number"),t.get("vin_number"),
                  t.get("descripcion"),t.get("creado_por"),t.get("tecnico"),
                  "Sí" if t.get("atendido") else "No",
                  "Sí" if t.get("reporte_enviado") else "No",
                  t.get("reporte") or "—",
                  str(t.get("fecha_creacion") or ""),
                  str(t.get("fecha_atencion") or ""),
                  str(t.get("fecha_reporte") or "")]
            for c,v in enumerate(vals,1):
                cell=ws4.cell(r,c,v); cell.alignment=LEFT
                if r%2==0: cell.fill=GRIS
        widths(ws4)

        # ── Hoja 5: Reporte_Cierre_Tickets ────────────────────────────────────
        ws5 = wb.create_sheet("Reporte_Cierre_Tickets")
        c5 = ["Ticket #","Unidad","VIN","Problema Reportado","Creado Por",
              "Técnico Asignado","Fecha Creación","Fecha Atención",
              "Actividad","Estado Actividad","Inicio Trabajo","Fin Trabajo",
              "Comentario Técnico","Reporte Final del Técnico",
              "Fecha Reporte Final","Ticket Cerrado"]
        hdr(ws5, 1, c5)
        cierre = execute_read(
            "SELECT t.ticket_num,t.unit_number,t.vin_number,t.descripcion,"
            "t.creado_por,t.tecnico,t.fecha_creacion,t.fecha_atencion,"
            "a.actividad_id,a.estado,a.fecha_inicio,a.fecha_fin,"
            "a.comentario,t.reporte,t.fecha_reporte,t.atendido "
            "FROM tickets t LEFT JOIN asignaciones a ON a.ticket_id=t.id "
            "ORDER BY t.ticket_num DESC") or []
        for r,row in enumerate(cierre,2):
            vals=[row.get("ticket_num"),row.get("unit_number"),row.get("vin_number"),
                  row.get("descripcion"),row.get("creado_por"),row.get("tecnico"),
                  str(row.get("fecha_creacion") or ""),str(row.get("fecha_atencion") or ""),
                  row.get("actividad_id") or "—",row.get("estado") or "—",
                  str(row.get("fecha_inicio") or ""),str(row.get("fecha_fin") or ""),
                  row.get("comentario") or "—",row.get("reporte") or "—",
                  str(row.get("fecha_reporte") or ""),
                  "Sí" if row.get("atendido") else "No"]
            for c,v in enumerate(vals,1):
                cell=ws5.cell(r,c,v); cell.alignment=LEFT
                if r%2==0: cell.fill=GRIS
        widths(ws5)

        buf = io.BytesIO()
        wb.save(buf); buf.seek(0)
        fecha = datetime.now().strftime("%Y%m%d_%H%M")
        return StreamingResponse(buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=reporte_maestro_{fecha}.xlsx"})

    except Exception as e:
        print(f"Error reporte-excel: {e}")
        import traceback; traceback.print_exc()
        return {"error": str(e)}
