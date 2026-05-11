from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import asyncio
from db import execute_read
import json
from datetime import datetime

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            sols = len(execute_read("SELECT id FROM asignaciones WHERE estado='solicitado'"))
            tickets = len(execute_read("SELECT id FROM tickets WHERE atendido=FALSE"))
            ahora = datetime.now().isoformat()
            await websocket.send_json({"sols": sols, "tickets": tickets, "time": ahora})
            await asyncio.sleep(30)
    except WebSocketDisconnect:
        pass
