"""Shared pytest fixtures."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from activity_engine.core.actions import ActionStatus, ActionType
from activity_engine.core.decisions import EnforcementMode
from activity_engine.core.events import (
    ActivityEvent,
    ApplicationInfo,
    BrowserInfo,
    EventSource,
    EventType,
    NetworkInfo,
)
from activity_engine.core.policies import (
    BedtimePolicy,
    EscalationPolicy,
    FocusPolicy,
    PolicyDocument,
)
from activity_engine.engine.event_engine import EventEngine


@pytest.fixture
def default_policy() -> PolicyDocument:
    """A default policy with a few blocked and allowed targets."""
    return PolicyDocument(
        version="test-v1",
        focus=FocusPolicy(
            enabled=True,
            allowed_domains=["classroom.google.com", "docs.google.com", "*.google.com"],
            blocked_domains=["youtube.com", "facebook.com", "tiktok.com"],
            allowed_apps=["Chrome"],
            blocked_apps=["Discord", "Steam"],
        ),
        escalation=EscalationPolicy(
            level_1_delay_seconds=5,
            level_2_delay_seconds=10,
            level_3_violation_threshold=3,
        ),
        bedtime=BedtimePolicy(enabled=False, start_time="22:30"),
    )


@pytest.fixture
def empty_policy() -> PolicyDocument:
    """A policy with nothing enabled."""
    return PolicyDocument(
        focus=FocusPolicy(enabled=False),
        bedtime=BedtimePolicy(enabled=False),
    )


def make_event(
    source: EventSource = EventSource.PROCESS,
    event_type: EventType = EventType.APP_FOCUSED,
    domain: str | None = None,
    app: str | None = None,
    process: str | None = None,
    device_id: str = "device-test",
    student_id: str | None = "student-test",
    timestamp: datetime | None = None,
) -> ActivityEvent:
    """Factory helper for canonical events used across tests."""
    return ActivityEvent(
        student_id=student_id,
        device_id=device_id,
        timestamp=timestamp or datetime.now(UTC),
        source=source,
        type=event_type,
        browser=BrowserInfo(domain=domain),
        application=ApplicationInfo(name=app, process=process),
    )


@pytest.fixture
def make_browser_event():
    """Factory for browser events."""

    def _make(domain: str, event_type: EventType = EventType.WEB_NAVIGATION) -> ActivityEvent:
        return make_event(
            source=EventSource.BROWSER,
            event_type=event_type,
            domain=domain,
        )

    return _make


@pytest.fixture
def make_app_event():
    """Factory for application events."""

    def _make(app: str, process: str | None = None) -> ActivityEvent:
        return make_event(
            source=EventSource.PROCESS,
            event_type=EventType.APP_FOCUSED,
            app=app,
            process=process or app.lower(),
        )

    return _make


@pytest.fixture
def event_engine() -> EventEngine:
    """A bare EventEngine for normalization tests."""
    return EventEngine(device_id="device-test", student_id="student-test")