# asistencia/horarios_routes.py
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
    """Obtiene los horarios para una semana específica"""
    from db import get_db_connection
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if username:
        cursor.execute("""
            SELECT * FROM horarios 
            WHERE semana = ? AND username = ?
        """, (semana, username))
    else:
        cursor.execute("SELECT * FROM horarios WHERE semana = ?", (semana,))
    
    horarios = cursor.fetchall()
    conn.close()
    
    resultado = []
    for row in horarios:
        resultado.append(dict(row))
    
    return resultado


@router.post("/api/horarios/")
async def guardar_horarios(horarios: HorarioBulk):
    """Guarda o actualiza horarios en masa"""
    from db import get_db_connection
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    guardados = 0
    for h in horarios.registros:
        cursor.execute("""
            INSERT OR REPLACE INTO horarios (username, fecha, semana, hora_entrada, hora_salida)
            VALUES (?, ?, ?, ?, ?)
        """, (h.username, h.fecha, h.semana, h.hora_entrada, h.hora_salida))
        guardados += 1
    
    conn.commit()
    conn.close()
    
    return {"mensaje": f"{guardados} horarios guardados"}


@router.get("/api/horarios/resumen")
async def get_resumen_asistencia(semana: str):
    """Obtiene el resumen de asistencia para la semana"""
    from db import get_db_connection
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Obtener horarios configurados
    cursor.execute("SELECT * FROM horarios WHERE semana = ?", (semana,))
    horarios = cursor.fetchall()
    horarios_dict = {}
    for h in horarios:
        horarios_dict[f"{h['username']}_{h['fecha']}"] = {
            "entrada": h["hora_entrada"], 
            "salida": h["hora_salida"]
        }
    
    # Obtener asistencias reales de la semana
    try:
        semana_date = datetime.strptime(semana, "%Y-%m-%d")
        fin_semana = semana_date + timedelta(days=7)
        
        cursor.execute("""
            SELECT username, fecha, hora, lat_tecnico, lon_tecnico, distancia_m, dentro_radio
            FROM asistencia 
            WHERE fecha >= ? AND fecha < ?
            ORDER BY fecha, hora
        """, (semana, fin_semana.strftime("%Y-%m-%d")))
    except:
        cursor.execute("""
            SELECT username, fecha, hora, lat_tecnico, lon_tecnico, distancia_m, dentro_radio
            FROM asistencia 
            WHERE fecha LIKE ?
            ORDER BY fecha, hora
        """, (semana + '%',))
    
    asistencias = cursor.fetchall()
    conn.close()
    
    # Procesar resumen
    resumen = []
    for a in asistencias:
        username = a["username"]
        fecha = a["fecha"]
        hora = a["hora"]
        
        horario = horarios_dict.get(f"{username}_{fecha}", {})
        
        # Calcular retardo si hay horario configurado
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
