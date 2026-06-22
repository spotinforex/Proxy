import logging
from fastapi.websockets import WebSocket, WebSocketDisconnect

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("websocket")

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)

    async def broadcast(self, data: dict):
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception as e:
                logger.warning(f"WebSocket broadcast failed: {e}")
