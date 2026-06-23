# backend/routers/alarmas_router.py
import re
from fastapi import APIRouter, Depends, HTTPException
from db import execute_read
from auth import verify_token

router = APIRouter(prefix="/api/alarmas", tags=["alarmas"])


def _normalizar_query(q: str) -> str:
    """
    Normaliza el término de búsqueda:
    - Elimina letras/espacios del inicio antes de dígitos  (A00128 → 00128)
    - Strip de espacios generales
    """
    q = q.strip()
    # Si empieza con letras seguidas de dígitos, quitar el prefijo de letras
    q = re.sub(r'^[A-Za-z\s]+(?=\d)', '', q)
    return q.strip()


@router.get("/buscar")
def buscar_alarma(q: str = "", current_user=Depends(verify_token)):
    """
    Busca alarmas por código exacto o parcial, o por título.
    ?q=00128   → busca código
    ?q=A00128  → normaliza a 00128 automáticamente
    ?q=coolant → busca en título
    Devuelve hasta 20 resultados.
    """
    if not q.strip():
        raise HTTPException(status_code=400, detail="Parámetro 'q' es requerido")

    term = _normalizar_query(q)
    if not term:
        term = q.strip()

    rows = execute_read(
        """
        SELECT
            codigo, titulo, activacion, control_unidad,
            condicion_reset, notas, acciones_correctivas,
            referencia_alarma, alarmas_relacionadas, figuras
        FROM alarmas_reefer
        WHERE codigo LIKE %s OR titulo LIKE %s
        ORDER BY codigo ASC
        LIMIT 20
        """,
        (f"%{term}%", f"%{term}%"),
    )
    return rows


@router.get("/seed")
def seed_alarmas(current_user=Depends(verify_token)):
    """
    Endpoint de emergencia: fuerza la carga de alarmas.json en la tabla si está vacía.
    Solo admins.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")

    import json, pathlib
    from db import execute_write, execute_read as er

    count = er("SELECT COUNT(*) as n FROM alarmas_reefer")
    n = count[0]["n"] if count else 0
    if n > 0:
        return {"ok": True, "mensaje": f"La tabla ya tiene {n} alarmas. No se hizo nada."}

    json_path = pathlib.Path(__file__).parent.parent / "alarmas.json"
    if not json_path.exists():
        raise HTTPException(status_code=500, detail="alarmas.json no encontrado en el servidor")

    alarmas = json.loads(json_path.read_text(encoding="utf-8"))
    for a in alarmas:
        execute_write(
            """
            INSERT INTO alarmas_reefer
                (codigo, titulo, activacion, control_unidad,
                 condicion_reset, notas, acciones_correctivas,
                 referencia_alarma, alarmas_relacionadas, figuras)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            ON DUPLICATE KEY UPDATE titulo=VALUES(titulo)
            """,
            (
                a["codigo"],
                a["titulo"],
                a.get("activacion"),
                a.get("control_unidad"),
                a.get("condicion_reset"),
                a.get("notas"),
                json.dumps(a.get("acciones_correctivas") or [], ensure_ascii=False),
                json.dumps(a.get("referencia_alarma"), ensure_ascii=False),
                json.dumps(a.get("alarmas_relacionadas") or [], ensure_ascii=False),
                json.dumps(a.get("figuras") or [], ensure_ascii=False),
            ),
        )
    return {"ok": True, "mensaje": f"{len(alarmas)} alarmas cargadas correctamente"}


@router.get("/{codigo}")
def get_alarma(codigo: str, current_user=Depends(verify_token)):
    """Devuelve una alarma por código exacto."""
    codigo_norm = _normalizar_query(codigo)
    rows = execute_read(
        """
        SELECT
            codigo, titulo, activacion, control_unidad,
            condicion_reset, notas, acciones_correctivas,
            referencia_alarma, alarmas_relacionadas, figuras
        FROM alarmas_reefer
        WHERE codigo = %s
        LIMIT 1
        """,
        (codigo_norm or codigo,),
    )
    if not rows:
        raise HTTPException(status_code=404, detail=f"Alarma {codigo} no encontrada")
    return rows[0]
