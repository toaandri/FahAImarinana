from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ....notifications import alert_manager

router = APIRouter(prefix="/alerts", tags=["Alertes"])


@router.websocket("/ws")
async def alerts_websocket(websocket: WebSocket):
    await alert_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        alert_manager.disconnect(websocket)
