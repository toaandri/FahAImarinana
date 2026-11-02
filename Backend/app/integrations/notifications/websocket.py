from fastapi import WebSocket


class AlertManager:
    def __init__(self):
        self.connections: dict[WebSocket, tuple[int, str]] = {}

    async def connect(self, websocket: WebSocket, *, scope: tuple[int, str], subprotocol: str | None = None):
        await websocket.accept(subprotocol=subprotocol)
        self.connections[websocket] = scope

    def disconnect(self, websocket: WebSocket):
        self.connections.pop(websocket, None)

    async def broadcast(self, payload: dict, *, scope: tuple[int, str]):
        for connection, recipient_scope in tuple(self.connections.items()):
            if recipient_scope != scope:
                continue
            try:
                await connection.send_json(payload)
            except Exception:
                self.disconnect(connection)


alert_manager = AlertManager()
