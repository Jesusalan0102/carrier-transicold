from fastapi import APIRouter, Depends
from db import execute_read
from auth import verify_token
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/kpis")
def get_kpis(current_user=Depends(verify_token)):
    try:
        total_usuarios = execute_read("SELECT COUNT(*) as total FROM users")[0]["total"]
        total_activos  = execute_read("SELECT COUNT(*) as total FROM users WHERE is_active=1")[0]["total"]

        total_asignaciones = execute_read("SELECT COUNT(*) as total FROM asignaciones")[0]["total"]

        inicio_mes = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        completadas_mes = execute_read(
            "SELECT COUNT(*) as total FROM asignaciones WHERE estado='completada' AND fecha_entrega >= %s",
            (inicio_mes,)
        )[0]["total"]

        porcentaje = round((total_activos / total_usuarios * 100) if total_usuarios > 0 else 0, 2)

        return {
            "total_usuarios": total_usuarios,
            "usuarios_activos": total_activos,
            "total_asignaciones": total_asignaciones,
            "asignaciones_completadas_mes": completadas_mes,
            "porcentaje_actividad": porcentaje
        }
    except Exception as e:
        print(f"Error en kpis: {e}")
        return {
            "total_usuarios": 0,
            "usuarios_activos": 0,
            "total_asignaciones": 0,
            "asignaciones_completadas_mes": 0,
            "porcentaje_actividad": 0
        }

@router.get("/stats_tecnicos")
def get_stats_tecnicos(current_user=Depends(verify_token)):
    try:
        tecnicos = execute_read("SELECT id, username, is_active FROM users WHERE role='tecnico'")
        if not tecnicos:
            tecnicos = execute_read("SELECT id, username, is_active FROM users WHERE rol='tecnico'")

        resultado = []
        hace_30_dias = datetime.now() - timedelta(days=30)

        for t in tecnicos:
            uid = t["id"]

            total_a = execute_read(
                "SELECT COUNT(*) as total FROM asignaciones WHERE tecnico=%s",
                (t["username"],)
            )[0]["total"]

            completadas = execute_read(
                "SELECT COUNT(*) as total FROM asignaciones WHERE tecnico=%s AND estado='completada'",
                (t["username"],)
            )[0]["total"]

            asistencias = execute_read(
                "SELECT COUNT(*) as total FROM asistencia_registros WHERE user_id=%s AND fecha >= %s",
                (uid, hace_30_dias)
            )[0]["total"]

            resultado.append({
                "id": uid,
                "nombre": t["username"],
                "total_asignaciones": total_a,
                "completadas": completadas,
                "asistencias_30dias": asistencias,
                "activo": bool(t["is_active"])
            })

        return resultado
    except Exception as e:
        print(f"Error en stats_tecnicos: {e}")
        return []
