"""
search_router.py
-----------------
Búsqueda global (Ctrl+K): un solo endpoint que busca en paralelo dentro de
unidades, tickets y evidencias/reportes, y devuelve resultados agrupados
por categoría con lo justo para armar una lista de resultados en el
frontend (título, subtítulo, y a dónde navegar al hacer click).

No busca en TODO — deliberadamente deja fuera cosas como usuarios o
asignaciones individuales, que ya tienen sus propias pantallas de listado
con filtro local. El objetivo de Ctrl+K es "encontrar la unidad/ticket
correcto rápido", no reemplazar cada tabla existente.
"""
from fastapi import APIRouter, Depends, Query
from db import execute_read
from auth import verify_token

router = APIRouter(prefix="/api/search", tags=["search"])

MAX_POR_CATEGORIA = 8


@router.get("/global")
def busqueda_global(q: str = Query(..., min_length=2), current_user: dict = Depends(verify_token)):
    termino = q.strip()
    like = f"%{termino}%"

    # ── Unidades: por número económico, VIN, o cualquier número de serie ──
    unidades = execute_read(
        """
        SELECT unit_number, id_lote, vin_number, reefer_model
        FROM unidades
        WHERE unit_number LIKE %s OR vin_number LIKE %s OR id_lote LIKE %s
           OR reefer_serial LIKE %s OR engine_serial LIKE %s OR compressor_serial LIKE %s
        ORDER BY unit_number
        LIMIT %s
        """,
        (like, like, like, like, like, like, MAX_POR_CATEGORIA)
    )

    # ── Tickets: por número, descripción, o unidad ─────────────────────────
    tickets_rows = execute_read(
        "SELECT ticket_num, unit_number, descripcion, atendido, reporte_enviado "
        "FROM tickets WHERE CAST(ticket_num AS CHAR) LIKE %s OR descripcion LIKE %s "
        "OR unit_number LIKE %s ORDER BY ticket_num DESC LIMIT %s",
        (like, like, like, MAX_POR_CATEGORIA)
    )
    # Los técnicos solo ven sus propios tickets, igual que en /api/tickets/
    if current_user["role"] not in ("admin", "lider"):
        tickets_rows = execute_read(
            """SELECT t.ticket_num, t.unit_number, t.descripcion, t.atendido, t.reporte_enviado
               FROM tickets t
               JOIN asignaciones a ON t.id = a.ticket_id
               WHERE a.tecnico = %s
                 AND (CAST(t.ticket_num AS CHAR) LIKE %s OR t.descripcion LIKE %s OR t.unit_number LIKE %s)
               ORDER BY t.ticket_num DESC LIMIT %s""",
            (current_user["username"], like, like, like, MAX_POR_CATEGORIA)
        )

    # ── Evidencias / reportes: por nombre de archivo o unidad ──────────────
    evidencias = execute_read(
        "SELECT id, nombre_archivo, unit_number, tecnico, created_at FROM evidencias "
        "WHERE nombre_archivo LIKE %s OR unit_number LIKE %s "
        "ORDER BY created_at DESC LIMIT %s",
        (like, like, MAX_POR_CATEGORIA)
    )

    return {
        "query": termino,
        "unidades": [
            {
                "titulo": u["unit_number"],
                "subtitulo": " · ".join(filter(None, [u.get("reefer_model"), u.get("vin_number")])),
                "url": f"/app/unidades?ficha={u['unit_number']}",
            }
            for u in unidades
        ],
        "tickets": [
            {
                "titulo": f"Ticket #{t['ticket_num']} — {t['unit_number']}",
                "subtitulo": (t.get("descripcion") or "")[:80],
                "estado": "cerrado" if t.get("reporte_enviado") else ("atendido" if t.get("atendido") else "pendiente"),
                "url": f"/app/tickets?abrir={t['ticket_num']}",
            }
            for t in tickets_rows
        ],
        "evidencias": [
            {
                "titulo": e["nombre_archivo"],
                "subtitulo": f"Unidad {e['unit_number']} · {e.get('tecnico') or ''}",
                "url": f"/app/unidades?ficha={e['unit_number']}",
            }
            for e in evidencias
        ],
    }
