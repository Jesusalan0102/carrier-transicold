# backend/asistencia/horarios_routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta

router = APIRouter()

class HorarioRegistro(BaseModel):
    username: str
    fecha: str
    semana: str
    hora_entrada: str
    hora_salida: str

class HorarioBulk(BaseModel):
    registros: List[HorarioRegistro]


@router.get("/api/horarios/")
async def get_horarios(semana: str, username: Optional[str] = None):
    from db import execute_read
    
    if username:
        registros = execute_read("SELECT * FROM horarios WHERE semana = %s AND username = %s", (semana, username))
    else:
        registros = execute_read("SELECT * FROM horarios WHERE semana = %s", (semana,))
    
    return registros


@router.post("/api/horarios/")
async def guardar_horarios(horarios: HorarioBulk):
    from db import execute_write
    
    guardados = 0
    for h in horarios.registros:
        execute_write("""
            INSERT INTO horarios (username, fecha, semana, hora_entrada, hora_salida)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            hora_entrada = VALUES(hora_entrada),
            hora_salida = VALUES(hora_salida)
        """, (h.username, h.fecha, h.semana, h.hora_entrada, h.hora_salida))
        guardados += 1
    
    return {"mensaje": f"{guardados} horarios guardados"}


@router.get("/api/horarios/resumen")
async def get_resumen_asistencia(semana: str):
    from db import execute_read
    
    # Obtener horarios configurados
    horarios = execute_read("SELECT * FROM horarios WHERE semana = %s", (semana,))
    horarios_dict = {}
    for h in horarios:
        horarios_dict[f"{h['username']}_{h['fecha']}"] = {"entrada": h["hora_entrada"], "salida": h["hora_salida"]}
    
    # Obtener asistencias reales
    try:
        semana_date = datetime.strptime(semana, "%Y-%m-%d")
        fin_semana = semana_date + timedelta(days=7)
        asistencias = execute_read("""
            SELECT username, fecha, hora, lat_tecnico, lon_tecnico, distancia_m, dentro_radio
            FROM asistencia 
            WHERE fecha >= %s AND fecha < %s
            ORDER BY fecha, hora
        """, (semana, fin_semana.strftime("%Y-%m-%d")))
    except:
        asistencias = execute_read("SELECT username, fecha, hora, lat_tecnico, lon_tecnico, distancia_m, dentro_radio FROM asistencia WHERE fecha LIKE %s ORDER BY fecha, hora", (semana + '%',))
    
    # Procesar resumen
    resumen = []
    for a in asistencias:
        username = a["username"]
        fecha = a["fecha"]
        hora = a["hora"]
        
        horario = horarios_dict.get(f"{username}_{fecha}", {})
        
        retardo = 0
        if horario.get("entrada") and hora > horario["entrada"]:
            try:
                entrada_dt = datetime.strptime(horario["entrada"], "%H:%M")
                hora_dt = datetime.strptime(hora, "%H:%M")
                retardo = (hora_dt - entrada_dt).seconds // 60
            except:
                pass
        
        resumen.append({
            "username": username,
            "fecha": fecha,
            "hora_checkin": hora,
            "lat_tecnico": a["lat_tecnico"],
            "lon_tecnico": a["lon_tecnico"],
            "distancia_m": a["distancia_m"],
            "dentro_radio": bool(a["dentro_radio"]),
            "hora_programada": horario.get("entrada", ""),
            "retardo_min": retardo if retardo > 0 else 0
        })
    
    return resumen
