"""FastAPI WebSocket server for the Activity Engine.

Exposes:
  GET  /                    — health check
  POST /api/session/start   — start a monitoring session
  POST /api/session/end     — end the active session
  GET  /api/state           — current StateSnapshot as JSON
  GET  /api/metrics         — engine metrics
  GET  /api/events          — recent activity events
  POST /api/telemetry       — feed raw telemetry from frontend
  WS   /ws                  — realtime broadcast (state, decision, action, event)

Usage:
    pip install ".[server]"
    uvicorn src.activity_engine.server:app --reload --port 8000
"""

from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .engine.facade import ActivityEngine
from .transport.dto import MessageType, WireMessage
from .transport.protocol import (
    build_message,
    event_message,
    state_message,
    error_message,
)
from .utils.ids import short_id

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Global engine & connection manager
# ---------------------------------------------------------------------------

_engine: ActivityEngine | None = None
_session_id: str | None = None


class ConnectionManager:
    """Manages active WebSocket connections and broadcasts messages."""

    def __init__(self) -> None:
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.append(ws)
        logger.info("ws_connect clients=%d", len(self.active))

    def disconnect(self, ws: WebSocket) -> None:
        self.active.remove(ws)
        logger.info("ws_disconnect clients=%d", len(self.active))

    async def broadcast(self, message: WireMessage) -> None:
        data = message.model_dump_json()
        disconnected: list[WebSocket] = []
        for ws in self.active:
            try:
                await ws.send_text(data)
            except Exception:  # noqa: BLE001
                disconnected.append(ws)
        for ws in disconnected:
            self.active.remove(ws)


manager = ConnectionManager()


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):  # type: ignore[type-arg]
    global _engine
    _engine = ActivityEngine(student_id="student-001")
    logger.info("activity_engine=initialized")
    yield
    logger.info("activity_engine=shutdown")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Flowsink Activity Engine API",
    description="Student Activity Monitoring & Focus Control Engine — REST + WebSocket",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------


@app.get("/", tags=["health"])
async def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "flowsink-activity-engine",
        "version": "0.1.0",
        "timestamp": datetime.now(UTC).isoformat(),
        "ws_clients": len(manager.active),
    }


@app.post("/api/session/start", tags=["session"])
async def start_session(student_id: str = "student-001") -> dict[str, Any]:
    global _engine, _session_id
    if _engine is None:
        _engine = ActivityEngine(student_id=student_id)

    _session_id = _engine.start_session()

    snapshot = _engine.current_state()
    if snapshot:
        await manager.broadcast(state_message(snapshot))

    return {
        "session_id": _session_id,
        "student_id": student_id,
        "started_at": datetime.now(UTC).isoformat(),
    }


@app.post("/api/session/end", tags=["session"])
async def end_session() -> dict[str, Any]:
    global _session_id
    if _engine is None:
        return {"status": "no_active_engine"}

    _engine.end_session()
    ended_session = _session_id
    _session_id = None

    await manager.broadcast(
        build_message(MessageType.STATE, {"state": "UNKNOWN", "session_id": ended_session})
    )
    return {"status": "ended", "session_id": ended_session}


@app.get("/api/state", tags=["monitoring"])
async def get_state() -> dict[str, Any]:
    if _engine is None:
        return {"state": "UNKNOWN", "session_id": None}

    snapshot = _engine.current_state()
    if snapshot is None:
        return {"state": "UNKNOWN", "session_id": _session_id}

    return {
        **snapshot.model_dump(),
        "session_active": _session_id is not None,
    }


@app.get("/api/metrics", tags=["monitoring"])
async def get_metrics() -> dict[str, Any]:
    if _engine is None:
        return {}
    return _engine.metrics()


@app.get("/api/events", tags=["monitoring"])
async def get_events(limit: int = 50) -> dict[str, Any]:
    if _engine is None:
        return {"events": []}
    events = await _engine.recent_events(limit=limit)
    return {"events": [e.model_dump() for e in events], "count": len(events)}


@app.post("/api/telemetry", tags=["monitoring"])
async def feed_telemetry(raw: dict[str, Any]) -> dict[str, Any]:
    """Accept a raw telemetry event from the frontend and process it."""
    if _engine is None:
        return {"status": "error", "detail": "Engine not initialized"}

    event = await _engine.feed_raw(raw)
    if event is None:
        return {"status": "dropped", "reason": "deduplication or validation"}

    snapshot = _engine.current_state()

    # Broadcast updated state to all WS clients
    if snapshot:
        await manager.broadcast(state_message(snapshot))

    await manager.broadcast(event_message(event))

    return {
        "status": "processed",
        "event_id": event.event_id,
        "state": snapshot.state.value if snapshot else "UNKNOWN",
    }


# ---------------------------------------------------------------------------
# WebSocket endpoint
# ---------------------------------------------------------------------------


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket) -> None:
    await manager.connect(ws)

    # Send initial hello with current state
    hello_payload: dict[str, Any] = {
        "message": "Connected to Flowsink Activity Engine",
        "session_id": _session_id,
        "ws_clients": len(manager.active),
    }
    if _engine is not None:
        snapshot = _engine.current_state()
        if snapshot:
            hello_payload["state"] = snapshot.model_dump()

    await ws.send_text(
        build_message(MessageType.HELLO, hello_payload).model_dump_json()
    )

    try:
        while True:
            # Keep connection alive by reading ping messages from client
            raw_text = await ws.receive_text()
            try:
                msg = json.loads(raw_text)
                if msg.get("type") == "ping":
                    await ws.send_text(
                        build_message(MessageType.PONG, {"ts": datetime.now(UTC).isoformat()}).model_dump_json()
                    )
                elif msg.get("type") == "telemetry" and msg.get("payload"):
                    # Client can also push telemetry over WS
                    if _engine:
                        event = await _engine.feed_raw(msg["payload"])
                        if event:
                            snapshot = _engine.current_state()
                            if snapshot:
                                await manager.broadcast(state_message(snapshot))
                            await manager.broadcast(event_message(event))
            except (json.JSONDecodeError, KeyError):
                pass
    except WebSocketDisconnect:
        manager.disconnect(ws)
