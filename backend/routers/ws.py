from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import asyncio, json
from db import execute_read
from datetime import datetime
from zoneinfo import ZoneInfo
from jose import JWTError, jwt
import os

TZ = ZoneInfo("America/Tijuana")
router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "carrier_secret_key_2024_change_in_production")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")


# ── Loop reference (set on first WebSocket connection) ───────────────────────
_main_loop = None

# ── Connection Manager ────────────────────────────────────────────────────────
class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        global _main_loop
        import asyncio
        if _main_loop is None:
            _main_loop = asyncio.get_event_loop()
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


# ── Textos de notificación push por evento ───────────────────────────────────
_PUSH_LABELS = {
    "solicitud_nueva":      ("📋 Solicitud de actividad",  "Un técnico solicitó una actividad"),
    "asignacion_nueva":     ("✅ Actividad asignada",       "Se asignó una nueva actividad"),
    "solicitud_aprobada":   ("👍 Solicitud aprobada",       "Tu solicitud fue aprobada"),
    "actividad_iniciada":   ("▶️ Actividad iniciada",      "Un técnico inició una actividad"),
    "actividad_completada": ("🏁 Actividad completada",    "Una actividad fue completada"),
    "ticket_nuevo":         ("🎫 Nuevo ticket",             "Se creó un nuevo ticket de servicio"),
}


async def notify(event: str, payload: dict = None):
    """Emite evento por WebSocket (app abierta) y Push Notification (segundo plano)."""
    data = {
        "type": event,
        "payload": payload or {},
        "time": datetime.now(TZ).isoformat(),
    }
    # 1. Broadcast WebSocket a todas las pestañas abiertas
    await manager.broadcast(data)

    # 2. Push Notification para usuarios en segundo plano (hilo separado)
    if event in _PUSH_LABELS:
        title, base_body = _PUSH_LABELS[event]
        # Enriquecer el body con datos del payload
        p = payload or {}
        parts = []
        if p.get("tecnico"):    parts.append(p["tecnico"])
        if p.get("unidad"):     parts.append(f"Unidad {p['unidad']}")
        if p.get("unit_number"): parts.append(f"Unidad {p['unit_number']}")
        body = " · ".join(parts) if parts else base_body
        import asyncio, concurrent.futures
        loop = asyncio.get_event_loop()
        try:
            from routers.push_router import send_push_to_all
            await loop.run_in_executor(
                None,
                lambda: send_push_to_all(title, body, tag=event)
            )
        except Exception:
            pass


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(default=None)):
    if not token:
        await websocket.close(code=1008)
        return
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not payload.get("sub"):
            raise ValueError("Token sin usuario")
    except (JWTError, ValueError):
        await websocket.close(code=1008)
        return

    await manager.connect(websocket)
    try:
        # Enviar estado inicial al conectarse
        sols    = len(execute_read("SELECT id FROM asignaciones WHERE estado='solicitado'"))
        tickets = len(execute_read("SELECT id FROM tickets WHERE atendido=FALSE"))
        await websocket.send_json({
            "type": "status",
            "sols": sols,
            "tickets": tickets,
            "time": datetime.now(TZ).isoformat(),
        })
        # Mantener viva la conexión con heartbeat cada 30s
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
