from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import asyncio, json, logging
from db import execute_read
from datetime import datetime
from zoneinfo import ZoneInfo
from jose import JWTError, jwt
import os

logger = logging.getLogger(__name__)
TZ = ZoneInfo("America/Tijuana")
router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "carrier_secret_key_2024_change_in_production")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")


# ── Connection Manager ────────────────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active:
            self.active.remove(ws)

    async def broadcast(self, data: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


# ── Textos de notificación push por evento ────────────────────────────────────
_PUSH_LABELS = {
    "solicitud_nueva":      ("📋 Solicitud de actividad",  "Un técnico solicitó una actividad"),
    "asignacion_nueva":     ("✅ Actividad asignada",       "Se asignó una nueva actividad"),
    "solicitud_aprobada":   ("👍 Solicitud aprobada",       "Tu solicitud fue aprobada"),
    "actividad_iniciada":   ("▶️ Actividad iniciada",      "Un técnico inició una actividad"),
    "actividad_completada": ("🏁 Actividad completada",    "Una actividad fue completada"),
    "ticket_nuevo":         ("🎫 Nuevo ticket",             "Se creó un nuevo ticket de servicio"),
    "corriendo_6h":         ("⏱️ 6 horas corriendo",        "Una unidad lleva 6 horas corriendo"),
}


async def notify(event: str, payload: dict = None):
    """Emite evento por WebSocket Y envía push notification."""
    data = {
        "type": event,
        "payload": payload or {},
        "time": datetime.now(TZ).isoformat(),
    }
    # 1. WebSocket broadcast
    await manager.broadcast(data)

    # 2. Push en executor para no bloquear
    if event in _PUSH_LABELS:
        title, base_body = _PUSH_LABELS[event]
        p = payload or {}
        parts = []
        if p.get("tecnico"):     parts.append(p["tecnico"])
        if p.get("unidad"):      parts.append(f"Unidad {p['unidad']}")
        if p.get("unit_number"): parts.append(f"Unidad {p['unit_number']}")
        body = " · ".join(parts) if parts else base_body

        loop = asyncio.get_event_loop()
        from routers.push_router import send_push_to_all
        await loop.run_in_executor(None, send_push_to_all, title, body, event)


UMBRAL_HORAS_CORRIENDO = 6

async def monitor_corriendo_6h():
    """
    Tarea en segundo plano (independiente de conexiones WebSocket activas).
    Cada 60s revisa las actividades 'Corriendo' en curso y, si alguna ya lleva
    6+ horas y no se ha notificado, dispara WebSocket + push y marca la bandera
    para no repetir el aviso.
    """
    while True:
        try:
            rows = execute_read(
                "SELECT a.id, a.unidad, a.fecha_inicio "
                "FROM asignaciones a "
                "WHERE a.actividad_id='Corriendo' AND a.estado='en_proceso' "
                "AND a.alerta_6h_enviada=0 "
                "AND a.fecha_inicio <= (NOW() - INTERVAL %s HOUR)",
                (UMBRAL_HORAS_CORRIENDO,)
            )
            for r in rows:
                from db import execute_write
                execute_write(
                    "UPDATE asignaciones SET alerta_6h_enviada=1 WHERE id=%s",
                    (r["id"],)
                )
                await notify("corriendo_6h", {
                    "asignacion_id": r["id"],
                    "unidad": r["unidad"],
                    "unit_number": r["unidad"],
                    "fecha_inicio": str(r["fecha_inicio"]),
                    "horas": UMBRAL_HORAS_CORRIENDO,
                })
                logger.info(f"[corriendo_6h] Alerta enviada — unidad {r['unidad']} (asignacion {r['id']})")
        except Exception as e:
            logger.error(f"monitor_corriendo_6h error: {e}")
        await asyncio.sleep(60)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(default=None)):
    if not token:
        await websocket.accept()
        await websocket.close(code=1008)
        return
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not payload.get("sub"):
            raise ValueError("Token sin usuario")
    except (JWTError, ValueError):
        await websocket.accept()
        await websocket.close(code=1008)
        return

    await manager.connect(websocket)
    try:
        sols    = len(execute_read("SELECT id FROM asignaciones WHERE estado='solicitado'"))
        tickets = len(execute_read("SELECT id FROM tickets WHERE atendido=FALSE"))
        await websocket.send_json({
            "type": "status",
            "sols": sols,
            "tickets": tickets,
            "time": datetime.now(TZ).isoformat(),
        })
        while True:
            await asyncio.sleep(30)
            sols    = len(execute_read("SELECT id FROM asignaciones WHERE estado='solicitado'"))
            tickets = len(execute_read("SELECT id FROM tickets WHERE atendido=FALSE"))
            await websocket.send_json({
                "type": "status",
                "sols": sols,
                "tickets": tickets,
                "time": datetime.now(TZ).isoformat(),
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)
