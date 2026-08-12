"""Regression tests for policy-resolution fail-fast wiring in the facade.

Covers:
- PHASE 4: policy resolution — bundled default when config/policy.yaml absent
- PHASE 4: policy resolution — explicit config/policy.yaml takes precedence
- PHASE 5: Windows stub adapters raise NotImplementedError (legacy guards)
- PHASE 6: browser-active endpoint contract vs. ExtensionBrowserMonitor
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from activity_engine.core.actions import ActionStatus, ActionType
from activity_engine.core.decisions import EnforcementMode
from activity_engine.core.policies import PolicyDocument
from activity_engine.engine.facade import ActivityEngine
from activity_engine.adapters.mock.action_executor import MockActionExecutor
from activity_engine.config.models import Config, RuntimeConfig
from activity_engine.core.errors import ConfigurationError
from activity_engine.services.browser_events import normalize_extension_event
from activity_engine.services.browser_state import BrowserStateStore


# ---------------------------------------------------------------------------
# Policy resolution — fail-fast (PHASE 4)
# ---------------------------------------------------------------------------

class TestPolicyResolution:
    """The facade must never silently degrade to an empty PolicyDocument."""

    def test_bundled_default_when_no_policy_file(self, tmp_path: Path) -> None:
        """When config/policy.yaml does not exist, the bundled default is used."""
        config = Config(runtime=RuntimeConfig(mode=EnforcementMode.DRY_RUN))
        engine = ActivityEngine(config=config, executor=MockActionExecutor())
        assert isinstance(engine.policy, PolicyDocument)
        # Bundled default has version "1" and focus enabled.
        assert engine.policy.version == "1"
        assert engine.policy.focus.enabled is True

    def test_explicit_policy_file_takes_precedence(self, tmp_path: Path) -> None:
        """When an explicit policy.yaml exists, PolicyLoader resolves it."""
        policy_yaml = tmp_path / "custom_policy.yaml"
        policy_yaml.write_text(
            'version: "42"\n'
            "focus:\n"
            "  enabled: true\n"
            "  blocked_domains:\n"
            "    - evil.com\n"
            "escalation:\n"
            "  level_1_delay_seconds: 5\n"
            "  level_2_delay_seconds: 15\n"
            "  level_3_violation_threshold: 2\n"
            "bedtime:\n"
            '  enabled: false\n'
            '  start_time: "21:00"\n'
        )
        config = Config(
            runtime=RuntimeConfig(mode=EnforcementMode.DRY_RUN),
            policy_file=str(policy_yaml),
        )
        engine = ActivityEngine(config=config, executor=MockActionExecutor())
        assert engine.policy.version == "42"
        assert "evil.com" in engine.policy.focus.blocked_domains

    def test_invalid_policy_file_raises(self, tmp_path: Path) -> None:
        """A malformed policy YAML must raise ConfigurationError, not silently
        fall back to an empty policy."""
        bad_yaml = tmp_path / "bad_policy.yaml"
        bad_yaml.write_text("focus:\n  enabled: true\n  this_is: [invalid\n")

        config = Config(
            runtime=RuntimeConfig(mode=EnforcementMode.DRY_RUN),
            policy_file=str(bad_yaml),
        )
        with pytest.raises((ConfigurationError, Exception)):
            ActivityEngine(config=config, executor=MockActionExecutor())

    def test_no_silent_empty_policy(self, tmp_path: Path) -> None:
        """The old silent fallback to PolicyDocument() must not exist.

        When an explicit policy path does not exist, the facade falls back
        to the bundled default — never to an empty PolicyDocument() which
        would disable all enforcement.
        """
        missing = tmp_path / "does_not_exist.yaml"
        config = Config(
            runtime=RuntimeConfig(mode=EnforcementMode.DRY_RUN),
            policy_file=str(missing),
        )
        engine = ActivityEngine(config=config, executor=MockActionExecutor())
        # Must NOT be an empty PolicyDocument — must be the bundled default.
        assert engine.policy.version == "1"
        assert engine.policy.focus.enabled is True
        assert "youtube.com" in engine.policy.focus.blocked_domains


# ---------------------------------------------------------------------------
# Windows stub adapters — LEGACY (PHASE 5)
# ---------------------------------------------------------------------------

class TestWindowsStubAdapters:
    """Windows stub adapters must raise NotImplementedError (never silently
    no-op).  This guards against accidental use on non-Windows platforms."""

    def test_windows_action_executor_is_legacy(self) -> None:
        import activity_engine.adapters.windows.action_executor as mod

        assert "LEGACY" in (mod.__doc__ or "")

        executor = mod.WindowsActionExecutor()
        with pytest.raises(NotImplementedError):
            asyncio.run(executor.warn({"action_id": "x"}))

    def test_windows_browser_monitor_is_legacy(self) -> None:
        import activity_engine.adapters.windows.browser_monitor as mod

        assert "LEGACY" in (mod.__doc__ or "")

        monitor = mod.WindowsBrowserMonitor()
        with pytest.raises(NotImplementedError):
            asyncio.run(monitor.start())

    def test_windows_browser_monitor_methods_raise(self) -> None:
        from activity_engine.adapters.windows.browser_monitor import (
            WindowsBrowserMonitor,
        )

        monitor = WindowsBrowserMonitor()
        with pytest.raises(NotImplementedError):
            asyncio.run(monitor.get_active_tabs())


# ---------------------------------------------------------------------------
# Browser /api/browser/active contract (PHASE 6)
# ---------------------------------------------------------------------------

class TestBrowserActiveContract:
    """Verify the end-to-end contract:
    server endpoint -> ExtensionBrowserMonitor._poll_http ->
    MonitoringService._poll_browser."""

    def test_normalized_event_has_required_fields(self) -> None:
        """normalize_extension_event must emit a dict that EventEngine can
        consume (kind + browser.name/tab_id/domain)."""
        raw: dict[str, Any] = {
            "kind": "browser_navigation",
            "device_id": "DEV-1",
            "tab_id": "10",
            "domain": "classroom.google.com",
            "url": "https://classroom.google.com/",
        }
        event = normalize_extension_event(raw)
        assert event is not None
        assert event["kind"] == "browser_navigation"
        assert "browser" in event
        assert event["browser"]["name"] is not None
        assert event["browser"]["domain"] == "classroom.google.com"
        assert event["browser"]["tab_id"] == "10"

    def test_server_response_shape_matches_adapter(self) -> None:
        """The server's /api/browser/active returns {'tabs': [...], 'count': N}.

        ExtensionBrowserMonitor._poll_http() does data.get('tabs').
        BrowserStateStore.get_active_tabs() returns dicts with name, tab_id,
        domain, url, title, updated_at — all consumed by MonitoringService.
        """
        store = BrowserStateStore()
        store.record_event({
            "kind": "browser_navigation",
            "device_id": "DEV-1",
            "tab_id": "10",
            "domain": "classroom.google.com",
            "url": "https://classroom.google.com/",
        })
        tabs = store.get_active_tabs("DEV-1")
        # MonitoringService._poll_browser accesses tabs[0].get("name"/"tab_id"/"domain")
        assert len(tabs) == 1
        tab = tabs[0]
        assert tab["name"] is not None
        assert tab["tab_id"] == "10"
        assert tab["domain"] == "classroom.google.com"

    @pytest.mark.asyncio
    async def test_http_mode_returns_empty_when_offline(self) -> None:
        """When the backend server is not running, the adapter must return
        an empty list (fault isolation), not crash."""
        from activity_engine.adapters.extension.browser_monitor import (
            ExtensionBrowserMonitor,
        )

        monitor = ExtensionBrowserMonitor(api_url="http://127.0.0.1:59999")
        tabs = await monitor.get_active_tabs()
        assert tabs == []

    @pytest.mark.asyncio
    async def test_end_to_end_browser_violation(self) -> None:
        """A blocked-domain browser_navigation event through the facade
        must trigger a WARNING state and an executed WARN action."""
        config = Config(runtime=RuntimeConfig(mode=EnforcementMode.ENFORCE))
        executor = MockActionExecutor()
        engine = ActivityEngine(
            config=config, executor=executor, student_id="ST-BROWSER"
        )
        engine.start_session()

        await engine.feed_raw({
            "kind": "browser_navigation",
            "browser": {"domain": "youtube.com", "tab_id": "tab-x"},
        })
        await asyncio.sleep(0.01)

        state = engine.current_state()
        assert state is not None
        from activity_engine.core.states import ActivityState
        assert state.state == ActivityState.WARNING
        assert len(executor.executed) == 1
        assert executor.executed[0]["action"] == ActionType.WARN.value
        assert executor.executed[0]["status"] == ActionStatus.SUCCESS.value

        engine.end_session()
