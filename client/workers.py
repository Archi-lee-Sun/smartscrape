"""Network workers. No worker in this module ever accesses a Qt widget."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
import websockets
from PyQt6.QtCore import QThread, pyqtSignal


API_BASE_URL = "http://127.0.0.1:8001"
PIPELINE_WEBSOCKET_URL = "ws://127.0.0.1:8001/ws/pipeline/run"


class PipelineWorker(QThread):
    """Receive pipeline events on a background thread, one signal at a time."""

    event_received = pyqtSignal(dict)
    failed = pyqtSignal(str)
    stream_closed = pyqtSignal()

    def __init__(self) -> None:
        super().__init__()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._websocket: Any = None
        self._stopping = False

    def run(self) -> None:
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._receive_events())
        except Exception as exc:  # Network failures must become safe UI state.
            if not self._stopping:
                self.failed.emit(str(exc))
        finally:
            if self._loop is not None:
                self._loop.close()
            self._loop = None
            self._websocket = None
            self.stream_closed.emit()

    async def _receive_events(self) -> None:
        async with websockets.connect(PIPELINE_WEBSOCKET_URL) as websocket:
            self._websocket = websocket
            async for message in websocket:
                import json

                event = json.loads(message)
                if not isinstance(event, dict):
                    raise ValueError("The pipeline sent an invalid event.")
                self.event_received.emit(event)
                if event.get("event_type") == "completed":
                    break

    def stop(self) -> None:
        """Close the socket from the GUI thread without blocking that thread."""

        self._stopping = True
        if self._loop is not None and self._websocket is not None:
            asyncio.run_coroutine_threadsafe(self._websocket.close(), self._loop)


class ApiWorker(QThread):
    """Run one REST operation off the GUI thread."""

    succeeded = pyqtSignal(str, object)
    failed = pyqtSignal(str, str)

    def __init__(self, operation: str, payload: Any = None) -> None:
        super().__init__()
        self.operation = operation
        self.payload = payload

    def run(self) -> None:
        try:
            with httpx.Client(base_url=API_BASE_URL, timeout=15.0) as client:
                response = self._request(client)
                if response.status_code == 404 and self.operation == "detail":
                    self.succeeded.emit(self.operation, None)
                    return
                response.raise_for_status()
                self.succeeded.emit(self.operation, response.json())
        except Exception as exc:
            self.failed.emit(self.operation, str(exc))

    def _request(self, client: httpx.Client) -> httpx.Response:
        if self.operation == "save":
            return client.post("/vault/save", json=self.payload)
        if self.operation == "entries":
            return client.get("/vault/entries")
        if self.operation == "search":
            return client.get("/vault/search", params={"q": str(self.payload)})
        if self.operation == "detail":
            return client.get(f"/vault/entries/{int(self.payload)}")
        raise ValueError(f"Unsupported API operation: {self.operation}")
