"""Integration tests for the Activity Engine facade."""

from __future__ import annotations

import asyncio
import pytest

from activity_engine.config.models import Config, RuntimeConfig
from activity_engine.core.actions import ActionType
from activity_engine.core.decisions import EnforcementMode
from activity_engine.core.events import EventSource, EventType
from activity_engine.core.states import ActivityState
from activity_engine.engine.facade import ActivityEngine
from activity_engine.adapters.mock.action_executor import MockActionExecutor

@pytest.mark.asyncio
async def test_end_to_end_pipeline_dry_run() -> None:
    # 1. Config & facade setup in dry_run (default)
    config = Config(runtime=RuntimeConfig(mode=EnforcementMode.DRY_RUN))
    executor = MockActionExecutor()
    engine = ActivityEngine(config=config, executor=executor, student_id="ST001")

    # Start session
    session_id = engine.start_session()
    assert session_id

    # 2. Feed allowed browser event -> FOCUS state, no action
    raw = {
        "kind": "browser_navigation",
        "browser": {"domain": "classroom.google.com", "tab_id": "tab-1"},
    }
    event = await engine.feed_raw(raw)
    assert event is not None
    assert event.browser.domain == "classroom.google.com"
    assert event.type == EventType.WEB_NAVIGATION
    assert event.source == EventSource.BROWSER
    state = engine.current_state()
    assert state
    assert state.state == ActivityState.FOCUS
    assert len(executor.executed) == 0

    # 3. Feed blocked browser event -> WARNING state
    # Use different tab_id to avoid debouncing deduplication
    raw2 = {
        "kind": "browser_navigation",
        "browser": {"domain": "youtube.com", "tab_id": "tab-2"},
    }
    event2 = await engine.feed_raw(raw2)
    assert event2 is not None
    assert event2.browser.domain == "youtube.com"
    assert event2.type == EventType.WEB_NAVIGATION
    assert event2.source == EventSource.BROWSER
    state2 = engine.current_state()
    assert state2
    assert state2.state == ActivityState.WARNING
    assert len(executor.executed) == 0
    assert engine.metrics()["action_engine"]["actions_not_executed"] == 1

    engine.end_session()

@pytest.mark.asyncio
async def test_violations_use_policy_engine_canonical_source() -> None:
    """Violations returned by the facade must come from the PolicyEngine,
    not the repository (which is never populated), and must carry the
    active session id."""
    config = Config(runtime=RuntimeConfig(mode=EnforcementMode.ENFORCE))
    executor = MockActionExecutor()
    engine = ActivityEngine(config=config, executor=executor, student_id="ST-VIOL")
    session_id = engine.start_session()

    await engine.feed_raw(
        {
            "kind": "browser_navigation",
            "browser": {"domain": "youtube.com", "tab_id": "tab-v1"},
        }
    )

    violations = await engine.violations()
    assert len(violations) == 1
    v = violations[0]
    assert v.student_id == "ST-VIOL"
    assert v.session_id == session_id
    assert v.domain == "youtube.com"
    assert v.level == "level_1"

    engine.end_session()

@pytest.mark.asyncio
async def test_events_are_stamped_with_session_id() -> None:
    """Every event stored in the repository must carry the active session id."""
    config = Config(runtime=RuntimeConfig(mode=EnforcementMode.DRY_RUN))
    executor = MockActionExecutor()
    engine = ActivityEngine(config=config, executor=executor, student_id="ST-SID")
    session_id = engine.start_session()

    await engine.feed_raw(
        {
            "kind": "browser_navigation",
            "browser": {"domain": "classroom.google.com", "tab_id": "tab-s1"},
        }
    )
    await engine.feed_raw(
        {
            "kind": "browser_navigation",
            "browser": {"domain": "docs.google.com", "tab_id": "tab-s2"},
        }
    )

    events = await engine.recent_events(limit=10)
    assert len(events) == 2
    assert all(e.session_id == session_id for e in events)
    assert all(e.device_id for e in events)

    engine.end_session()

@pytest.mark.asyncio
async def test_end_to_end_pipeline_enforce() -> None:
    # 1. Config & facade setup in enforce mode
    config = Config(runtime=RuntimeConfig(mode=EnforcementMode.ENFORCE))
    executor = MockActionExecutor()
    engine = ActivityEngine(config=config, executor=executor, student_id="ST001")

    engine.start_session()

    # 2. Feed blocked browser event -> triggers real action in mock adapter
    event = await engine.feed_raw(
        {
            "kind": "browser_navigation",
            "browser": {"domain": "facebook.com", "tab_id": "tab-1"},
        }
    )
    assert event
    # Yield control briefly for the async subscription route to execute
    await asyncio.sleep(0.01)

    state = engine.current_state()
    assert state
    assert state.state == ActivityState.WARNING
    assert len(executor.executed) == 1
    assert executor.executed[0]["action"] == ActionType.WARN

    engine.end_session()