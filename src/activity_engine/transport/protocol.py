"""WebSocket protocol — message envelope factory and validation.

Phase 1 defines the wire contract (JSON over WebSocket). A real Starlette /
FastAPI WebSocket server is a future extension point; this module provides
the protocol helpers that server will use.
"""

from __future__ import annotations

from datetime import UTC, datetime

from ..core.actions import ActionResult
from ..core.decisions import PolicyDecision
from ..core.events import ActivityEvent
from ..core.states import StateSnapshot
from ..utils.ids import short_id
from .dto import MessageType, WireMessage
from .serialization import to_jsonable

def build_message(
    message_type: MessageType,
    payload: object | None = None,
    message_id: str | None = None,
) -> WireMessage:
    """Create a wire message envelope."""
    return WireMessage(
        type=message_type,
        id=message_id or short_id(),
        timestamp=datetime.now(UTC),
        payload=to_jsonable(payload or {}),
    )

def event_message(event: ActivityEvent) -> WireMessage:
    """Wrap a canonical event for broadcast."""
    return build_message(MessageType.EVENT, event.model_dump())

def state_message(snapshot: StateSnapshot) -> WireMessage:
    """Wrap a state snapshot for broadcast."""
    return build_message(MessageType.STATE, snapshot.model_dump())

def decision_message(decision: PolicyDecision) -> WireMessage:
    """Wrap a policy decision for broadcast."""
    return build_message(MessageType.DECISION, decision.model_dump())

def action_message(result: ActionResult) -> WireMessage:
    """Wrap an action result for broadcast."""
    return build_message(MessageType.ACTION, result.model_dump())

def error_message(error_code: str, detail: str, message_id: str | None = None) -> WireMessage:
    """Wrap an error for broadcast."""
    return WireMessage(
        type=MessageType.ERROR,
        id=message_id or short_id(),
        timestamp=datetime.now(UTC),
        payload={"error": error_code, "detail": detail},
    )