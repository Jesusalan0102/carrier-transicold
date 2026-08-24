from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from db import execute_read, execute_write
from auth import verify_token
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo
import asyncio
TZ = ZoneInfo("America/Tijuana")

# ── Importación opcional de OneDrive ────────────────────────────────────────
try:
    from onedrive_service import sync_reporte_ticket
    ONEDRIVE_ENABLED = True
except ImportError:
    ONEDRIVE_ENABLED = False

EXTENSIONES_REPORTE_PERMITIDAS = {"pdf", "doc", "docx"}
MAX_REPORTE_BYTES = 20 * 1024 * 1024  # 20 MB

def _notify(event: str, payload: dict = None):
    """Emite evento WebSocket+Push desde endpoint síncrono."""
    import threading
    def _run():
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            from routers.ws import notify
            loop.run_until_complete(notify(event, payload))
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"_notify error: {e}")
        finally:
            loop.close()
    threading.Thread(target=_run, daemon=True).start()

router = APIRouter(prefix="/api/tickets", tags=["tickets"])

class TicketCreate(BaseModel):
    unit_number: str
    vin_number: Optional[str] = ""
    descripcion: str
    tecnico: str

# ── LISTAR ─────────────────────────────────────────────────────────────────
@router.get("/")
def listar_tickets(current_user=Depends(verify_token)):
    if current_user["role"] not in ("admin", "lider"):
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
    if current_user["role"] not in ("admin", "lider"):
        raise HTTPException(status_code=403, detail="Solo administradores y líderes")

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
async def enviar_reporte(
    ticket_id: int,
    reporte: str = Form(...),
    archivo: Optional[UploadFile] = File(None),
    current_user=Depends(verify_token),
):
    if not reporte.strip():
        raise HTTPException(status_code=400, detail="El reporte no puede estar vacío")
    ahora = datetime.now(TZ)

    # ── Archivo opcional (Word/PDF) — exclusivo de tickets ──────────────
    archivo_nombre = archivo_url = archivo_item_id = None
    if archivo is not None and archivo.filename:
        ext = archivo.filename.rsplit(".", 1)[-1].lower() if "." in archivo.filename else ""
        if ext not in EXTENSIONES_REPORTE_PERMITIDAS:
            raise HTTPException(status_code=400, detail="El reporte solo admite archivos PDF o Word (.pdf, .doc, .docx)")
        contenido = await archivo.read()
        if len(contenido) > MAX_REPORTE_BYTES:
            raise HTTPException(status_code=400, detail="El archivo no debe superar 20 MB")
        if not ONEDRIVE_ENABLED:
            raise HTTPException(status_code=503, detail="La subida de archivos no está disponible en este momento")

        rows = execute_read("SELECT ticket_num FROM tickets WHERE id=%s", (ticket_id,))
        if not rows:
            raise HTTPException(status_code=404, detail="Ticket no encontrado")
        ticket_num = rows[0]["ticket_num"]

        try:
            resultado = await asyncio.to_thread(sync_reporte_ticket, ticket_num, archivo.filename, contenido)
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"No se pudo subir el archivo a OneDrive: {e}")
        archivo_nombre  = archivo.filename
        archivo_url     = resultado.get("webUrl", "")
        archivo_item_id = resultado.get("item_id", "")

    # 1. Guardar texto del reporte (y archivo, si vino) y marcar ticket como completado
    execute_write(
        """UPDATE tickets
           SET reporte_enviado         = TRUE,
               reporte_texto           = %s,
               fecha_reporte           = %s,
               reporte_archivo_nombre  = COALESCE(%s, reporte_archivo_nombre),
               reporte_archivo_url     = COALESCE(%s, reporte_archivo_url),
               reporte_archivo_item_id = COALESCE(%s, reporte_archivo_item_id)
           WHERE id = %s""",
        (reporte.strip(), ahora, archivo_nombre, archivo_url, archivo_item_id, ticket_id)
    )

    # 2. Cerrar la asignación vinculada (estado → completada, comentario = reporte)
    execute_write(
        """UPDATE asignaciones
           SET estado     = 'completada',
               comentario = %s,
               fecha_fin  = %s
           WHERE ticket_id = %s AND estado != 'completada'""",
        (reporte.strip(), ahora, ticket_id)
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

