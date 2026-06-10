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


async def notify(event: str, payload: dict = None):
    """Llamar desde cualquier router para emitir un evento con sonido."""
    await manager.broadcast({
        "type": event,
        "payload": payload or {},
        "time": datetime.now(TZ).isoformat(),
    })


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
