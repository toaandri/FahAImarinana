from fastapi import WebSocket


class AlertManager:
    def __init__(self):
        self.connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket, subprotocol: str | None = None):
        await websocket.accept(subprotocol=subprotocol)
        self.connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.connections.discard(websocket)

    async def broadcast(self, payload: dict):
        disconnected = []
        for connection in tuple(self.connections):
            try:
                await connection.send_json(payload)
            except Exception:
                disconnected.append(connection)
        for connection in disconnected:
            self.disconnect(connection)


alert_manager = AlertManager()
