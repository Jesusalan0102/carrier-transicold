from fastapi import APIRouter, Depends
from db import execute_read
from auth import verify_token
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/kpis")
def get_kpis(current_user=Depends(verify_token)):
    try:
        total_usuarios  = execute_read("SELECT COUNT(*) as total FROM users")[0]["total"]
        total_asignaciones = execute_read("SELECT COUNT(*) as total FROM asignaciones")[0]["total"]
        completadas_mes = execute_read(
            "SELECT COUNT(*) as total FROM asignaciones WHERE estado='completada'"
        )[0]["total"]
        return {
            "total_usuarios": total_usuarios,
            "usuarios_activos": total_usuarios,
            "total_asignaciones": total_asignaciones,
            "asignaciones_completadas_mes": completadas_mes,
            "porcentaje_actividad": 100
        }
    except Exception as e:
        print(f"Error en kpis: {e}")
        return {"total_usuarios": 0, "usuarios_activos": 0, "total_asignaciones": 0,
                "asignaciones_completadas_mes": 0, "porcentaje_actividad": 0}

@router.get("/stats_tecnicos")
def get_stats_tecnicos(current_user=Depends(verify_token)):
    try:
        tecnicos = execute_read("SELECT id, username FROM users WHERE role='tecnico'")
        resultado = []
        for t in tecnicos:
            total_a    = execute_read("SELECT COUNT(*) as total FROM asignaciones WHERE tecnico=%s", (t["username"],))[0]["total"]
            completadas = execute_read("SELECT COUNT(*) as total FROM asignaciones WHERE tecnico=%s AND estado='completada'", (t["username"],))[0]["total"]
            resultado.append({
                "id": t["id"], "nombre": t["username"],
                "total_asignaciones": total_a, "completadas": completadas,
                "asistencias_30dias": 0, "activo": True
            })
        return resultado
    except Exception as e:
        print(f"Error en stats_tecnicos: {e}")
        return []
