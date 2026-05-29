from fastapi import APIRouter, Depends, HTTPException, Query
from db import execute_read, execute_write
from auth import verify_token
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/horarios", tags=["horarios"])


@router.get("/")
def get_horarios(
    semana: str = Query(...),
    current_user=Depends(verify_token)
):
    try:
        semana_date = datetime.strptime(semana, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido, usa YYYY-MM-DD")

    fin_semana = semana_date + timedelta(days=5)

    horarios = execute_read(
        "SELECT id, username, fecha, hora_entrada, hora_salida, semana "
        "FROM horarios WHERE fecha >= %s AND fecha <= %s ORDER BY fecha, username",
        (semana_date, fin_semana)
    )

    return [
        {
            "id": h["id"],
            "username": h["username"],
            "fecha": h["fecha"].isoformat() if hasattr(h["fecha"], "isoformat") else h["fecha"],
            "hora_entrada": h["hora_entrada"],
            "hora_salida": h["hora_salida"],
            "semana": h["semana"],
        }
        for h in horarios
    ]


@router.post("/")
def guardar_horarios(
    data: dict,
    current_user=Depends(verify_token)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden guardar horarios")

    registros = data.get("registros", [])
    if not registros:
        raise HTTPException(status_code=400, detail="No se enviaron registros")

    for reg in registros:
        existing = execute_read(
            "SELECT id FROM horarios WHERE username=%s AND fecha=%s",
            (reg["username"], reg["fecha"])
        )
        if existing:
            execute_write(
                "UPDATE horarios SET hora_entrada=%s, hora_salida=%s WHERE username=%s AND fecha=%s",
                (reg.get("hora_entrada", ""), reg.get("hora_salida", ""), reg["username"], reg["fecha"])
            )
        else:
            execute_write(
                "INSERT INTO horarios (username, fecha, hora_entrada, hora_salida, semana) "
                "VALUES (%s, %s, %s, %s, %s)",
                (reg["username"], reg["fecha"], reg.get("hora_entrada", ""), reg.get("hora_salida", ""), reg.get("semana", ""))
            )

    return {"mensaje": f"{len(registros)} horarios guardados"}


@router.get("/resumen")
def resumen_asistencia(
    semana: str = Query(...),
    current_user=Depends(verify_token)
):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")

    try:
        semana_date = datetime.strptime(semana, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido, usa YYYY-MM-DD")

    fin_semana = semana_date + timedelta(days=5)

    # Obtener técnicos
    tecnicos = execute_read(
        "SELECT username FROM usuarios WHERE role='tecnico'"
    )
    if not tecnicos:
        return []

    tecnicos_usernames = [t["username"] for t in tecnicos]
    placeholders = ",".join(["%s"] * len(tecnicos_usernames))

    # Obtener horarios de la semana
    horarios = execute_read(
        f"SELECT username, fecha, hora_entrada, hora_salida FROM horarios "
        f"WHERE fecha >= %s AND fecha <= %s AND username IN ({placeholders})",
        (semana_date, fin_semana, *tecnicos_usernames)
    )

    horario_dict = {}
    for h in horarios:
        fecha_str = h["fecha"].isoformat() if hasattr(h["fecha"], "isoformat") else h["fecha"]
        horario_dict[f"{h['username']}_{fecha_str}"] = h

    # Obtener asistencias aprobadas de la semana
    asistencias = execute_read(
        f"SELECT username, fecha, hora AS hora_checkin, distancia_m AS distancia_metros, dentro_radio AS aprobado FROM asistencia "
        f"WHERE fecha >= %s AND fecha <= %s AND username IN ({placeholders}) AND aprobado = 1",
        (semana_date, fin_semana, *tecnicos_usernames)
    )

    resultado = []
    for a in asistencias:
        fecha_str = a["fecha"].isoformat() if hasattr(a["fecha"], "isoformat") else a["fecha"]
        key = f"{a['username']}_{fecha_str}"
        horario = horario_dict.get(key)

        retardo_min = 0
        if horario and horario.get("hora_entrada"):
            try:
                hora_programada = datetime.strptime(horario["hora_entrada"], "%H:%M")
                hora_real = datetime.strptime(a["hora_checkin"], "%H:%M:%S")
                diff = (hora_real - hora_programada).total_seconds() / 60
                if diff > 0:
                    retardo_min = int(diff)
            except Exception:
                pass

        resultado.append({
            "username": a["username"],
            "fecha": fecha_str,
            "hora_checkin": a["hora_checkin"],
            "hora_programada": horario["hora_entrada"] if horario else None,
            "retardo_min": retardo_min,
            "distancia_metros": a["distancia_metros"],
            "aprobado": bool(a["aprobado"]),
        })

    return resultado
