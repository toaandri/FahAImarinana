from fastapi import WebSocket
from starlette.concurrency import run_in_threadpool


def validate_connection(token,scope):
    from ...database import SessionLocal
    from ...core.security import authenticate_token
    from ...core.rbac import authorize,Permission
    from ...core.errors import DomainError
    try:
        with SessionLocal() as db:
            user=authenticate_token(db,token)
            authorize(user,Permission.ALERTS_READ)
            return (user.newsroom_id,user.dataset)==scope
    except (DomainError,ValueError):
        return False


class AlertManager:
    def __init__(self,validator=None):
        self.connections: dict[WebSocket,tuple[int,str]]={}
        self.tokens: dict[WebSocket,str]={}
        self.validator=validator or validate_connection

    async def connect(self,websocket: WebSocket,*,scope: tuple[int,str],token: str,subprotocol: str|None=None):
        await websocket.accept(subprotocol=subprotocol)
        self.connections[websocket]=scope
        self.tokens[websocket]=token

    def disconnect(self,websocket: WebSocket):
        self.connections.pop(websocket,None)
        self.tokens.pop(websocket,None)

    async def broadcast(self,payload: dict,*,scope: tuple[int,str]):
        for connection,recipient_scope in tuple(self.connections.items()):
            if recipient_scope!=scope:
                continue
            try:
                if not await run_in_threadpool(self.validator,self.tokens[connection],recipient_scope):
                    await connection.close(code=1008)
                    self.disconnect(connection)
                    continue
                await connection.send_json(payload)
            except Exception:
                self.disconnect(connection)


alert_manager=AlertManager()
