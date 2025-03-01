from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict, List

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_connections:
            self.active_connections[room_id] = []
        self.active_connections[room_id].append(websocket)

    def disconnect(self, websocket: WebSocket, room_id: str):
        if room_id in self.active_connections:
            self.active_connections[room_id].remove(websocket)
            if not self.active_connections[room_id]:
                del self.active_connections[room_id]

    async def broadcast(self, message: str, room_id: str):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                await connection.send_text(message)

    async def send_message(self, message: str, room_id: str, websocket: WebSocket):
        if room_id in self.active_connections:
            for connection in self.active_connections[room_id]:
                if connection != websocket:
                    await connection.send_text(message)

manager = ConnectionManager()

@app.websocket("/room/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            print(data)
            await manager.send_message(data, room_id, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
        if room_id in manager.active_connections:
            await manager.broadcast(f"Client left the room", room_id)

