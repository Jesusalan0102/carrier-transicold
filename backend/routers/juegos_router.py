from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from auth import verify_token
from db import execute_read, execute_write

router = APIRouter(prefix="/api/juegos", tags=["juegos"])

JUEGOS_VALIDOS = {"memoria", "2048", "trivia"}


class PuntajeIn(BaseModel):
    juego: str
    puntaje: int


@router.post("/puntajes")
def guardar_puntaje(data: PuntajeIn, current_user=Depends(verify_token)):
    if data.juego not in JUEGOS_VALIDOS:
        raise HTTPException(status_code=400, detail="Juego no reconocido")
    if data.puntaje < 0 or data.puntaje > 999999:
        raise HTTPException(status_code=400, detail="Puntaje fuera de rango")
    execute_write(
        "INSERT INTO juegos_puntajes (username, juego, puntaje) VALUES (%s,%s,%s)",
        (current_user["username"], data.juego, data.puntaje)
    )
    return {"mensaje": "Puntaje guardado"}


@router.get("/puntajes/{juego}")
def top_puntajes(juego: str, current_user=Depends(verify_token)):
    if juego not in JUEGOS_VALIDOS:
        raise HTTPException(status_code=400, detail="Juego no reconocido")
    rows = execute_read(
        """SELECT jp.username, u.nombre_completo, jp.puntaje, jp.fecha
           FROM juegos_puntajes jp
           LEFT JOIN users u ON u.username = jp.username
           WHERE jp.juego = %s
           ORDER BY jp.puntaje DESC, jp.fecha ASC
           LIMIT 10""",
        (juego,)
    )
    return [
        {
            "nombre": r["nombre_completo"] or r["username"],
            "puntaje": r["puntaje"],
            "fecha": r["fecha"].strftime("%d/%m/%Y") if r["fecha"] else ""
        }
        for r in (rows or [])
    ]


@router.get("/mi-mejor/{juego}")
def mi_mejor_puntaje(juego: str, current_user=Depends(verify_token)):
    if juego not in JUEGOS_VALIDOS:
        raise HTTPException(status_code=400, detail="Juego no reconocido")
    rows = execute_read(
        "SELECT MAX(puntaje) AS mejor FROM juegos_puntajes WHERE juego=%s AND username=%s",
        (juego, current_user["username"])
    )
    return {"mejor": (rows[0]["mejor"] if rows and rows[0]["mejor"] is not None else 0)}
