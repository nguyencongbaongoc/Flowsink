"""Contract tests — validate wire formats and DTOs."""

from __future__ import annotations

import json

import pytest

from activity_engine.transport.dto import (
    ActionMessage,
    DecisionMessage,
    ErrorMessage,
    EventMessage,
    HelloMessage,
    MessageType,
    StateMessage,
    WireMessage,
)
from activity_engine.transport.serialization import dumps, loads, to_jsonable

class TestWireMessage:
    def test_wire_message_serialization(self) -> None:
        msg = WireMessage(
            type=MessageType.HELLO,
            id="msg-1",
            payload={"device": "PC", "student": "ST001"},
        )
        raw = dumps(msg)
        assert isinstance(raw, str)
        parsed = loads(raw)
        assert parsed["type"] == "hello"
        assert parsed["id"] == "msg-1"
        assert parsed["payload"]["device"] == "PC"

    def test_to_jsonable_nested_models(self) -> None:
        from activity_engine.core.events import ActivityEvent, BrowserInfo, EventSource, EventType

        event = ActivityEvent(
            device_id="PC",
            student_id="ST001",
            source=EventSource.BROWSER,
            type=EventType.WEB_NAVIGATION,
            browser=BrowserInfo(domain="classroom.google.com"),
        )
        obj = {"event": event}
        jsonable = to_jsonable(obj)
        assert jsonable["event"]["source"] == "browser"
        assert jsonable["event"]["browser"]["domain"] == "classroom.google.com"

class TestMessageTypes:
    def test_hello_message(self) -> None:
        msg = HelloMessage(payload={"device": "PC"})
        assert msg.type == MessageType.HELLO
        assert "device" in msg.payload

    def test_event_message(self) -> None:
        from activity_engine.core.events import ActivityEvent, BrowserInfo, EventSource, EventType

        event = ActivityEvent(
            device_id="PC",
            student_id="ST001",
            source=EventSource.BROWSER,
            type=EventType.WEB_NAVIGATION,
            browser=BrowserInfo(domain="youtube.com"),
        )
        msg = EventMessage(payload=event.model_dump())
        assert msg.type == MessageType.EVENT
        assert msg.payload["browser"]["domain"] == "youtube.com"

    def test_state_message(self) -> None:
        from activity_engine.core.states import ActivityState, StateSnapshot

        snapshot = StateSnapshot(
            student_id="ST001",
            device_id="PC",
            state=ActivityState.FOCUS,
        )
        msg = StateMessage(payload=snapshot.model_dump())
        assert msg.type == MessageType.STATE
        assert msg.payload["state"] == "FOCUS"

    def test_decision_message(self) -> None:
        from activity_engine.core.decisions import PolicyDecision, PolicyOutcome

        decision = PolicyDecision(
            event_id="evt-1",
            student_id="ST001",
            outcome=PolicyOutcome.WARNING,
        )
        msg = DecisionMessage(payload=decision.model_dump())
        assert msg.type == MessageType.DECISION
        assert msg.payload["outcome"] == "WARNING"

    def test_action_message(self) -> None:
        from activity_engine.core.actions import ActionResult, ActionStatus, ActionType

        result = ActionResult(
            action_id="act-1",
            action=ActionType.WARN,
            target="youtube.com",
            policy_id="focus-default",
            reason="FOCUS_POLICY",
            student_id="ST001",
            status=ActionStatus.SUCCESS,
        )
        msg = ActionMessage(payload=result.model_dump())
        assert msg.type == MessageType.ACTION
        assert msg.payload["action"] == "WARN"

    def test_error_message(self) -> None:
        msg = ErrorMessage(payload={"error": "INVALID_POLICY", "detail": "Field required"})
        assert msg.type == MessageType.ERROR
        assert msg.payload["error"] == "INVALID_POLICY"