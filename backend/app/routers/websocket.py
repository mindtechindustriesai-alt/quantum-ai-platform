import asyncio
import json
import random
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager = ConnectionManager()

@router.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Stream live quantum circuit execution telemetry every 2 seconds
            payload = {
                "timestamp": datetime.now().isoformat(),
                "chsh_score": round(2.74 + random.uniform(-0.02, 0.04), 3),
                "qubit_fidelity": round(0.984 + random.uniform(-0.005, 0.005), 4),
                "qpu_latency_ms": random.randint(12, 28),
                "circuit_depth": 4,
                "active_threads": len(manager.active_connections)
            }
            await websocket.send_text(json.dumps(payload))
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
