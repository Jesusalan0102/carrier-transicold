from fastapi import APIRouter, Depends, HTTPException
from db import execute_read, execute_write
from auth import verify_token
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/api/cluster", tags=["cluster"])

ACTIVIDADES_CARRIER = [
    "Cableado", "Programación", "Soldadura", "Check de fugas",
    "Vacío", "Cerrado", "Pre-viaje", "Horas Corridas",
    "Standby", "GPS", "Corriendo", "Inspección",
    "Accesorios", "Toma de Valores", "Evidencia", "Toma de Series",
]

class ClusterAsignacion(BaseModel):
    tecnicos: List[str]
    actividades: List[str]
    unidades: List[str]

@router.get("/tecnicos")
def listar_tecnicos(current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    return execute_read("SELECT username FROM users WHERE role IN ('tecnico','lider') ORDER BY username")

@router.get("/unidades")
def listar_unidades(current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    return execute_read("SELECT unit_number, id_lote FROM unidades ORDER BY id_lote, unit_number")

@router.get("/actividades")
def listar_actividades(current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    return [{"nombre": a} for a in ACTIVIDADES_CARRIER]

@router.post("/asignar")
def asignar_cluster(data: ClusterAsignacion, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    if not data.tecnicos or not data.actividades or not data.unidades:
        raise HTTPException(status_code=400, detail="Debes seleccionar técnicos, actividades y unidades")

    creadas = 0
    omitidas = 0

    for unidad in data.unidades:
        for actividad in data.actividades:
            for tecnico in data.tecnicos:
                # Verificar si ya existe esa combinación
                existe = execute_read(
                    "SELECT id FROM asignaciones WHERE unidad=%s AND actividad_id=%s AND tecnico=%s",
                    (unidad, actividad, tecnico)
                )
                if existe:
                    omitidas += 1
                    continue
                execute_write(
                    "INSERT INTO asignaciones (unidad, actividad_id, tecnico, estado) VALUES (%s,%s,%s,'pendiente')",
                    (unidad, actividad, tecnico)
                )
                creadas += 1

    return {
        "mensaje": f"{creadas} asignaciones creadas, {omitidas} omitidas (ya existían)",
        "creadas": creadas,
        "omitidas": omitidas
    }
