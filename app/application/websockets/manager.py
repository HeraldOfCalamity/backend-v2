# app/application/websockets/manager.py
from typing import Dict, Set
from fastapi import WebSocket
from collections import defaultdict
import json

class WSManager:
    def __init__(self):
        self.rooms: Dict[str, Set[WebSocket]] = defaultdict(set)

    async def connect(self, room: str, websocket: WebSocket):
        # NO websocket.accept() aquí
        self.rooms[room].add(websocket)

    def disconnect(self, room: str, websocket: WebSocket):
        if websocket in self.rooms.get(room, set()):
            self.rooms[room].remove(websocket)
        if not self.rooms[room]:
            self.rooms.pop(room, None)

    async def broadcast(self, room: str, message: dict):
        dead = []
        for ws in list(self.rooms.get(room, set())):
            try:
                await ws.send_text(json.dumps(message, default=str))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(room, ws)

manager = WSManager()
