from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import User, Asignacion, AsistenciaRegistro
from auth import get_current_user
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/kpis")
def get_kpis(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        total_usuarios = db.query(User).count()
        total_activos = db.query(User).filter(User.is_active == True).count()
        total_asignaciones = db.query(Asignacion).count()
        
        # Asignaciones completadas en el mes actual
        hoy = datetime.now()
        inicio_mes = datetime(hoy.year, hoy.month, 1)
        completadas_mes = db.query(Asignacion).filter(
            Asignacion.estado == "completada",
            Asignacion.fecha_entrega >= inicio_mes
        ).count()
        
        return {
            "total_usuarios": total_usuarios,
            "usuarios_activos": total_activos,
            "total_asignaciones": total_asignaciones,
            "asignaciones_completadas_mes": completadas_mes,
            "porcentaje_actividad": round((total_activos / total_usuarios * 100) if total_usuarios > 0 else 0, 2)
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
def get_stats_tecnicos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        tecnicos = db.query(User).filter(User.rol == "tecnico").all()
        resultado = []
        
        for tecnico in tecnicos:
            # Asignaciones del técnico
            total_asignaciones = db.query(Asignacion).filter(Asignacion.usuario_id == tecnico.id).count()
            completadas = db.query(Asignacion).filter(
                Asignacion.usuario_id == tecnico.id,
                Asignacion.estado == "completada"
            ).count()
            
            # Registros de asistencia en el último mes
            hace_30_dias = datetime.now() - timedelta(days=30)
            asistencias = db.query(AsistenciaRegistro).filter(
                AsistenciaRegistro.user_id == tecnico.id,
                AsistenciaRegistro.fecha >= hace_30_dias
            ).count()
            
            resultado.append({
                "id": tecnico.id,
                "nombre": tecnico.username,
                "total_asignaciones": total_asignaciones,
                "completadas": completadas,
                "asistencias_30dias": asistencias,
                "activo": tecnico.is_active
            })
        
        return resultado if resultado else []
    except Exception as e:
        print(f"Error en stats_tecnicos: {e}")
        return []
