# backend/routers/alarmas_router.py
from fastapi import APIRouter, Depends, HTTPException
from db import execute_read
from auth import verify_token

router = APIRouter(prefix="/api/alarmas", tags=["alarmas"])


@router.get("/buscar")
def buscar_alarma(q: str = "", current_user=Depends(verify_token)):
    """
    Busca alarmas por código exacto o parcial, o por título.
    ?q=00012  → busca por código
    ?q=coolant → busca en título
    Devuelve hasta 20 resultados.
    """
    if not q.strip():
        raise HTTPException(status_code=400, detail="Parámetro 'q' es requerido")

    term = q.strip()

    rows = execute_read(
        """
        SELECT
            codigo, titulo, activacion, control_unidad,
            condicion_reset, notas, acciones_correctivas,
            referencia_alarma, alarmas_relacionadas
        FROM alarmas_reefer
        WHERE codigo LIKE %s OR titulo LIKE %s
        ORDER BY codigo ASC
        LIMIT 20
        """,
        (f"%{term}%", f"%{term}%"),
    )
    return rows


@router.get("/{codigo}")
def get_alarma(codigo: str, current_user=Depends(verify_token)):
    """Devuelve una alarma por código exacto."""
    rows = execute_read(
        """
        SELECT
            codigo, titulo, activacion, control_unidad,
            condicion_reset, notas, acciones_correctivas,
            referencia_alarma, alarmas_relacionadas
        FROM alarmas_reefer
        WHERE codigo = %s
        LIMIT 1
        """,
        (codigo,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"Alarma {codigo} no encontrada")
    return rows[0]
