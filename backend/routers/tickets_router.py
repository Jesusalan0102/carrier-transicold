from fastapi import APIRouter, Depends, HTTPException
from db import execute_read, execute_write
from auth import verify_token
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo
import asyncio
TZ = ZoneInfo("America/Tijuana")

def _notify(event: str, payload: dict = None):
    try:
        from routers.ws import notify
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(notify(event, payload))
        else:
            loop.run_until_complete(notify(event, payload))
    except Exception:
        pass

router = APIRouter(prefix="/api/tickets", tags=["tickets"])

class TicketCreate(BaseModel):
    unit_number: str
    vin_number: Optional[str] = ""
    descripcion: str
    tecnico: str

class TicketReport(BaseModel):
    reporte: str

# ── LISTAR ─────────────────────────────────────────────────────────────────
@router.get("/")
def listar_tickets(current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        return execute_read(
            """SELECT t.* FROM tickets t
               JOIN asignaciones a ON t.id = a.ticket_id
               WHERE a.tecnico = %s
               ORDER BY t.ticket_num DESC""",
            (current_user["username"],)
        )
    return execute_read(
        """SELECT t.*, a.tecnico as tecnico_asig
           FROM tickets t
           LEFT JOIN asignaciones a ON t.id = a.ticket_id
           ORDER BY t.ticket_num DESC"""
    )

# ── SIGUIENTE NÚMERO ───────────────────────────────────────────────────────
@router.get("/next-number")
def next_ticket_number(current_user=Depends(verify_token)):
    res = execute_read("SELECT MAX(ticket_num) as max_num FROM tickets")
    if res and res[0]["max_num"] is not None:
        return {"ticket_num": res[0]["max_num"] + 1}
    return {"ticket_num": 1}

# ── CREAR ──────────────────────────────────────────────────────────────────
@router.post("/")
def crear_ticket(ticket: TicketCreate, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")

    from db import get_db_connection
    import pymysql

    conn = get_db_connection()
    if not conn:
        raise HTTPException(status_code=500, detail="No hay conexión con la base de datos")

    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cur:
            # Bloquea la tabla para que ninguna transacción concurrente
            # pueda leer el mismo MAX antes de que hagamos el INSERT.
            cur.execute("SELECT MAX(ticket_num) AS max_num FROM tickets FOR UPDATE")
            row = cur.fetchone()
            next_num = 1 if not row or row["max_num"] is None else row["max_num"] + 1

            cur.execute(
                "INSERT INTO tickets (ticket_num, unit_number, vin_number, descripcion, creado_por) "
                "VALUES (%s,%s,%s,%s,%s)",
                (next_num, ticket.unit_number, ticket.vin_number,
                 ticket.descripcion, current_user["username"])
            )
            ticket_id = cur.lastrowid

            cur.execute(
                "INSERT INTO asignaciones (unidad, actividad_id, tecnico, estado, ticket_id) "
                "VALUES (%s,%s,%s,'pendiente',%s)",
                (ticket.unit_number, f"Ticket #{next_num}", ticket.tecnico, ticket_id)
            )
            conn.commit()

        _notify("ticket_nuevo", {"unit_number": ticket.unit_number, "ticket_num": next_num})
        return {"mensaje": "Ticket creado", "ticket_num": next_num}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ── MARCAR ATENDIDO ────────────────────────────────────────────────────────
@router.put("/{ticket_id}/atender")
def atender_ticket(ticket_id: int, current_user=Depends(verify_token)):
    execute_write(
        "UPDATE tickets SET atendido=TRUE, fecha_atencion=%s WHERE id=%s",
        (datetime.now(TZ), ticket_id)
    )
    return {"mensaje": "Ticket marcado como atendido"}

# ── ENVIAR REPORTE ─────────────────────────────────────────────────────────
@router.put("/{ticket_id}/report")
def enviar_reporte(ticket_id: int, report: TicketReport, current_user=Depends(verify_token)):
    if not report.reporte.strip():
        raise HTTPException(status_code=400, detail="El reporte no puede estar vacío")
    ahora = datetime.now(TZ)

    # 1. Guardar texto del reporte y marcar ticket como completado
    execute_write(
        """UPDATE tickets
           SET reporte_enviado = TRUE,
               reporte_texto   = %s,
               fecha_reporte   = %s
           WHERE id = %s""",
        (report.reporte.strip(), ahora, ticket_id)
    )

    # 2. Cerrar la asignación vinculada (estado → completada, comentario = reporte)
    execute_write(
        """UPDATE asignaciones
           SET estado     = 'completada',
               comentario = %s,
               fecha_fin  = %s
           WHERE ticket_id = %s AND estado != 'completada'""",
        (report.reporte.strip(), ahora, ticket_id)
    )

    return {"mensaje": "Reporte enviado, ticket y actividad completados"}

# ── ELIMINAR (admin) ───────────────────────────────────────────────────────
@router.delete("/{ticket_id}")
def eliminar_ticket(ticket_id: int, current_user=Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores")
    execute_write("DELETE FROM asignaciones WHERE ticket_id=%s", (ticket_id,))
    execute_write("DELETE FROM tickets WHERE id=%s", (ticket_id,))
    return {"mensaje": "Ticket eliminado"}

