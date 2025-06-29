from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.client_sockets: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        print(f"🟢 Registrando socket para {client_id}")
        await websocket.accept()
        self.client_sockets[client_id] = websocket

    def disconnect(self, client_id: str):
        if client_id in self.client_sockets:
            del self.client_sockets[client_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

manager = ConnectionManager()