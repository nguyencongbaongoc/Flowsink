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