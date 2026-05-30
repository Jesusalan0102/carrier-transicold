from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from db import execute_read
from auth import verify_token
import io

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/kpis")
def get_kpis(current_user=Depends(verify_token)):
    """
    Devuelve los KPIs que el frontend del dashboard espera:
      - total_unidades
      - completadas
      - en_proceso
      - pendientes
      - avance  (porcentaje numérico, sin %)
    """
    try:
        total_unidades = execute_read(
            "SELECT COUNT(*) as total FROM unidades"
        )[0]["total"]

        completadas = execute_read(
            "SELECT COUNT(DISTINCT unidad) as total FROM asignaciones "
            "WHERE estado = 'completada'"
        )[0]["total"]

        en_proceso = execute_read(
            "SELECT COUNT(DISTINCT unidad) as total FROM asignaciones "
            "WHERE estado = 'en_proceso'"
        )[0]["total"]

        pendientes = execute_read(
            "SELECT COUNT(DISTINCT unidad) as total FROM asignaciones "
            "WHERE estado = 'pendiente'"
        )[0]["total"]

        avance = round((completadas / total_unidades * 100), 1) if total_unidades > 0 else 0

        return {
            "total_unidades":  total_unidades,
            "completadas":     completadas,
            "en_proceso":      en_proceso,
            "pendientes":      pendientes,
            "avance":          avance,
            # Campos legacy por si otros módulos los usan
            "total_usuarios":               execute_read("SELECT COUNT(*) as total FROM users")[0]["total"],
            "total_asignaciones":           execute_read("SELECT COUNT(*) as total FROM asignaciones")[0]["total"],
            "asignaciones_completadas_mes": execute_read(
                "SELECT COUNT(*) as total FROM asignaciones WHERE estado='completada'"
            )[0]["total"],
            "porcentaje_actividad": avance,
        }
    except Exception as e:
        print(f"Error en kpis: {e}")
        return {
            "total_unidades": 0, "completadas": 0,
            "en_proceso": 0, "pendientes": 0, "avance": 0,
            "total_usuarios": 0, "total_asignaciones": 0,
            "asignaciones_completadas_mes": 0, "porcentaje_actividad": 0,
        }


@router.get("/stats_tecnicos")
def get_stats_tecnicos(current_user=Depends(verify_token)):
    """
    Devuelve estadísticas por técnico.
    El frontend del barChart espera: tecnico, completadas, en_curso, pendientes
    """
    try:
        tecnicos = execute_read(
            "SELECT id, username FROM users WHERE role='tecnico'"
        )
        resultado = []
        for t in tecnicos:
            uname = t["username"]
            completadas = execute_read(
                "SELECT COUNT(*) as total FROM asignaciones "
                "WHERE tecnico=%s AND estado='completada'", (uname,)
            )[0]["total"]
            en_curso = execute_read(
                "SELECT COUNT(*) as total FROM asignaciones "
                "WHERE tecnico=%s AND estado='en_proceso'", (uname,)
            )[0]["total"]
            pendientes = execute_read(
                "SELECT COUNT(*) as total FROM asignaciones "
                "WHERE tecnico=%s AND estado='pendiente'", (uname,)
            )[0]["total"]
            resultado.append({
                "id":               t["id"],
                "nombre":           uname,
                "tecnico":          uname,   # ← el JS del barChart usa .tecnico
                "completadas":      completadas,
                "en_curso":         en_curso,
                "pendientes":       pendientes,
                "total_asignaciones": completadas + en_curso + pendientes,
                "asistencias_30dias": 0,
                "activo": True,
            })
        return resultado
    except Exception as e:
        print(f"Error en stats_tecnicos: {e}")
        return []


@router.get("/reporte-excel")
def reporte_excel(current_user=Depends(verify_token)):
    """Genera un reporte Excel con todas las asignaciones."""
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment
        from datetime import datetime

        asignaciones = execute_read(
            "SELECT a.id, a.unidad, a.actividad_id, a.tecnico, a.estado, "
            "a.fecha_creacion, a.comentario "
            "FROM asignaciones a ORDER BY a.fecha_creacion DESC"
        ) or []

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Asignaciones"

        headers = ["ID", "Unidad", "Actividad", "Técnico", "Estado",
                   "Fecha Creación", "Comentario"]
        header_fill = PatternFill("solid", fgColor="002B5B")
        header_font = Font(color="FFFFFF", bold=True)

        for col, h in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=h)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center")

        for row_idx, a in enumerate(asignaciones, 2):
            ws.cell(row=row_idx, column=1, value=a["id"])
            ws.cell(row=row_idx, column=2, value=a["unidad"])
            ws.cell(row=row_idx, column=3, value=a["actividad_id"])
            ws.cell(row=row_idx, column=4, value=a["tecnico"])
            ws.cell(row=row_idx, column=5, value=a["estado"])
            ws.cell(row=row_idx, column=6, value=str(a.get("fecha_creacion", "")))
            ws.cell(row=row_idx, column=7, value=a.get("comentario", ""))

        for col in ws.columns:
            max_len = max((len(str(c.value or "")) for c in col), default=10)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 40)

        buf = io.BytesIO()
        wb.save(buf)
        buf.seek(0)

        fecha = datetime.now().strftime("%Y%m%d")
        return StreamingResponse(
            buf,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=reporte_maestro_{fecha}.xlsx"}
        )
    except Exception as e:
        print(f"Error en reporte-excel: {e}")
        return {"error": str(e)}
