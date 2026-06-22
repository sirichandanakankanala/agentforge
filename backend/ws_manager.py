"""Simple WebSocket connection manager for streaming agent runs."""
from typing import Dict, List
from fastapi import WebSocket
from logger import get_logger

logger = get_logger("ws_manager")


class WebSocketManager:
    """Manage WebSocket connections grouped by agent run id or agent id."""

    def __init__(self):
        # key -> list of WebSocket connections
        self._connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, key: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(key, []).append(websocket)
        logger.info(f"WebSocket connected: {key} (total={len(self._connections[key])})")

    def disconnect(self, key: str, websocket: WebSocket) -> None:
        conns = self._connections.get(key, [])
        if websocket in conns:
            conns.remove(websocket)
            logger.info(f"WebSocket disconnected: {key} (remaining={len(conns)})")
        if not conns:
            self._connections.pop(key, None)

    async def send_json(self, key: str, message) -> None:
        conns = self._connections.get(key, [])
        for ws in list(conns):
            try:
                await ws.send_json(message)
            except Exception:
                # Best effort: ignore failures and disconnect stale sockets
                try:
                    ws.close()
                except Exception:
                    pass
                self.disconnect(key, ws)

    async def broadcast(self, message) -> None:
        # send to all connections
        for key in list(self._connections.keys()):
            await self.send_json(key, message)


# global instance
_ws_manager = None


def get_ws_manager() -> WebSocketManager:
    global _ws_manager
    if _ws_manager is None:
        _ws_manager = WebSocketManager()
    return _ws_manager
