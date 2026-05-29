from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any
from database import get_db
from models import Horario, Asistencia, Usuario
from auth import get_current_user

router = APIRouter(prefix="/api/horarios", tags=["horarios"])

@router.get("/")
async def get_horarios(
    semana: str = Query(..., description="Fecha de inicio de semana (Lunes)"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Obtener horarios de una semana específica"""
    try:
        semana_date = datetime.strptime(semana, "%Y-%m-%d").date()
        fin_semana = semana_date + timedelta(days=5)
        
        horarios = db.query(Horario).filter(
            Horario.fecha >= semana_date,
            Horario.fecha <= fin_semana
        ).all()
        
        return [
            {
                "id": h.id,
                "username": h.username,
                "fecha": h.fecha.isoformat(),
                "hora_entrada": h.hora_entrada,
                "hora_salida": h.hora_salida,
                "semana": h.semana
            }
            for h in horarios
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/")
async def guardar_horarios(
    data: dict,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Guardar múltiples horarios"""
    try:
        registros = data.get("registros", [])
        
        for reg in registros:
            existing = db.query(Horario).filter(
                Horario.username == reg["username"],
                Horario.fecha == reg["fecha"]
            ).first()
            
            if existing:
                existing.hora_entrada = reg.get("hora_entrada", "")
                existing.hora_salida = reg.get("hora_salida", "")
            else:
                nuevo = Horario(
                    username=reg["username"],
                    fecha=reg["fecha"],
                    hora_entrada=reg.get("hora_entrada", ""),
                    hora_salida=reg.get("hora_salida", ""),
                    semana=reg.get("semana", "")
                )
                db.add(nuevo)
        
        db.commit()
        return {"mensaje": f"{len(registros)} horarios guardados"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/resumen")
async def resumen_asistencia(
    semana: str = Query(..., description="Fecha de inicio de semana"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Resumen de asistencias reales con cálculo de retardos"""
    try:
        semana_date = datetime.strptime(semana, "%Y-%m-%d").date()
        fin_semana = semana_date + timedelta(days=5)
        
        # Obtener todos los técnicos
        tecnicos = db.query(Usuario).filter(Usuario.role == "tecnico").all()
        tecnicos_usernames = [t.username for t in tecnicos]
        
        # Obtener horarios programados
        horarios = db.query(Horario).filter(
            Horario.fecha >= semana_date,
            Horario.fecha <= fin_semana,
            Horario.username.in_(tecnicos_usernames)
        ).all()
        
        horario_dict = {}
        for h in horarios:
            horario_dict[f"{h.username}_{h.fecha.isoformat()}"] = h
        
        # Obtener asistencias reales
        asistencias = db.query(Asistencia).filter(
            Asistencia.fecha >= semana_date,
            Asistencia.fecha <= fin_semana,
            Asistencia.username.in_(tecnicos_usernames),
            Asistencia.aprobado == True
        ).all()
        
        resultado = []
        
        for asistencia in asistencias:
            key = f"{asistencia.username}_{asistencia.fecha.isoformat()}"
            horario = horario_dict.get(key)
            
            retardo_min = 0
            if horario and horario.hora_entrada:
                try:
                    hora_programada = datetime.strptime(horario.hora_entrada, "%H:%M")
                    hora_real = datetime.strptime(asistencia.hora_checkin, "%H:%M:%S")
                    diff = (hora_real - hora_programada).total_seconds() / 60
                    if diff > 0:
                        retardo_min = int(diff)
                except:
                    pass
            
            resultado.append({
                "username": asistencia.username,
                "fecha": asistencia.fecha.isoformat(),
                "hora_checkin": asistencia.hora_checkin,
                "hora_programada": horario.hora_entrada if horario else None,
                "retardo_min": retardo_min,
                "distancia_metros": asistencia.distancia_metros,
                "aprobado": asistencia.aprobado
            })
        
        return resultado
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
