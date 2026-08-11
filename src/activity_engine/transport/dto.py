"""Transport DTOs — wire formats for the websocket protocol."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

class MessageType(StrEnum):
    """WebSocket message types."""

    HELLO = "hello"
    EVENT = "event"
    STATE = "state"
    DECISION = "decision"
    ACTION = "action"
    PING = "ping"
    PONG = "pong"
    ERROR = "error"

class WireMessage(BaseModel):
    """Base envelope for all WebSocket messages."""

    model_config = ConfigDict(frozen=True)

    type: MessageType
    version: int = 1
    id: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: dict = Field(default_factory=dict)

class HelloMessage(WireMessage):
    """Client hello with device + student identity."""

    type: MessageType = MessageType.HELLO

class EventMessage(WireMessage):
    """A canonical ActivityEvent pushed to subscribers."""

    type: MessageType = MessageType.EVENT

class StateMessage(WireMessage):
    """A StateSnapshot pushed to subscribers."""

    type: MessageType = MessageType.STATE

class DecisionMessage(WireMessage):
    """A PolicyDecision pushed to subscribers."""

    type: MessageType = MessageType.DECISION

class ActionMessage(WireMessage):
    """An ActionResult pushed to subscribers."""

    type: MessageType = MessageType.ACTION

class ErrorMessage(WireMessage):
    """An error envelope."""

    type: MessageType = MessageType.ERROR