from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from starlette.websockets import WebSocket

log = logging.getLogger(__name__)


class AlertHub:
    def __init__(self) -> None:
        self._clients: set[WebSocket] = set()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._lock = asyncio.Lock()

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._clients.add(websocket)
        try:
            await websocket.send_json({"type": "connected", "message": "Alert stream connected"})
        except Exception:  # noqa: BLE001
            self._clients.discard(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._clients.discard(websocket)

    async def broadcast(self, payload: dict[str, Any]) -> None:
        if not self._clients:
            return
        dead = []
        for client in list(self._clients):
            try:
                await client.send_text(json.dumps(payload, ensure_ascii=False, default=str))
            except Exception:  # noqa: BLE001
                dead.append(client)
        for client in dead:
            self._clients.discard(client)

    def publish(self, event: dict[str, Any]) -> None:
        if self._loop is None or self._loop.is_closed():
            return
        try:
            asyncio.run_coroutine_threadsafe(
                self.broadcast({"type": "event", "event": event}),
                self._loop,
            )
        except RuntimeError:
            log.debug("Could not schedule alert broadcast", exc_info=True)
