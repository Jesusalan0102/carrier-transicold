from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
import asyncio
from db import execute_read
import json
from datetime import datetime
from zoneinfo import ZoneInfo
TZ = ZoneInfo("America/Tijuana")
from jose import JWTError, jwt
import os

router = APIRouter()

SECRET_KEY = os.getenv("SECRET_KEY", "carrier_secret_key_2024_change_in_production")
ALGORITHM  = os.getenv("ALGORITHM", "HS256")

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str = Query(default=None)):
    # Validar token antes de aceptar la conexión
    if not token:
        await websocket.close(code=1008)  # Policy Violation
        return
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if not payload.get("sub"):
            raise ValueError("Token sin usuario")
    except (JWTError, ValueError):
        await websocket.close(code=1008)
        return

    await websocket.accept()
    try:
        while True:
            sols = len(execute_read("SELECT id FROM asignaciones WHERE estado='solicitado'"))
            tickets = len(execute_read("SELECT id FROM tickets WHERE atendido=FALSE"))
            ahora = datetime.now(TZ).isoformat()
            await websocket.send_json({"sols": sols, "tickets": tickets, "time": ahora})
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        pass
