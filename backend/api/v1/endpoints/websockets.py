from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("websocket_connected", total_connections=len(self.active_connections))

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("websocket_disconnected", total_connections=len(self.active_connections))

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error("websocket_broadcast_error", error=str(e))

manager = ConnectionManager()

@router.websocket("/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # We can handle incoming messages if needed, mostly we just push
            logger.info("websocket_message_received", data=data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
