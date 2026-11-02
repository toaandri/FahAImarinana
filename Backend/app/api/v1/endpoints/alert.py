from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from ....database import get_db
from ....core.errors import AuthenticationError, ForbiddenError
from ....core.rbac import authorize, Permission as P
from ....core.security import authenticate_token
from ....integrations.notifications.websocket import alert_manager

router = APIRouter(prefix="/alerts", tags=["Alertes"])


@router.websocket("/ws")
async def alerts_websocket(websocket: WebSocket, db: Session = Depends(get_db)):
    authorization = websocket.headers.get("authorization", "")
    # Browser clients can use subprotocols: ["bearer", access_token]. No query-string secret.
    protocols = websocket.scope.get("subprotocols", [])
    protocol = None
    if authorization.lower().startswith("bearer "):
        token = authorization[7:]
    elif len(protocols) == 2 and protocols[0] == "bearer":
        token, protocol = protocols[1], "bearer"
    else:
        await websocket.close(code=1008)
        return
    try:
        user = await run_in_threadpool(authenticate_token, db, token)
    except AuthenticationError:
        await websocket.close(code=1008)
        return
    try:
        authorize(user,P.ALERTS_READ)
    except ForbiddenError:
        await websocket.close(code=1008)
        return
    scope = (user.newsroom_id, user.dataset)
    db.close()  # Return the connection to the pool before the long-lived socket.
    await alert_manager.connect(websocket, scope=scope, subprotocol=protocol)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        alert_manager.disconnect(websocket)
