# routes/ws_notifications.py

from fastapi import APIRouter, WebSocket
from websocket_manager.manager import manager

ws_router = APIRouter()

@ws_router.websocket("/ws/notifications/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    print(f"🔌 Conexión WebSocket iniciada para {client_id}")
    await manager.connect(websocket, client_id)
    try:
        while True:
            await websocket.receive_text()
    except Exception as e:
        print(f"⚠️ WebSocket desconectado: {e}")
        manager.disconnect(client_id)

