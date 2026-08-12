"""Tests for the Chrome browser-extension telemetry bridge."""

from __future__ import annotations

import asyncio

import pytest

from activity_engine.adapters.extension.browser_monitor import ExtensionBrowserMonitor
from activity_engine.services.browser_events import normalize_extension_event
from activity_engine.services.browser_state import BrowserStateStore


class TestNormalizeExtensionEvent:
    def test_valid_navigation(self) -> None:
        raw = {
            "kind": "browser_navigation",
            "timestamp": "2026-08-12T01:00:00Z",
            "device_id": "DESKTOP-TEST",
            "tab_id": "42",
            "domain": "youtube.com",
            "url": "https://youtube.com/watch?v=abc",
            "title": "YouTube",
        }
        event = normalize_extension_event(raw)
        assert event is not None
        assert event["kind"] == "browser_navigation"
        assert event["source"] == "extension"
        assert event["browser"]["domain"] == "youtube.com"
        # Query params stripped server-side as a second safety net.
        assert event["browser"]["url"] == "https://youtube.com/watch"
        assert event["metadata"]["extension_device_id"] == "DESKTOP-TEST"

    def test_invalid_scheme_dropped(self) -> None:
        raw = {
            "kind": "browser_navigation",
            "url": "chrome://settings",
            "domain": "chrome",
        }
        assert normalize_extension_event(raw) is None

    def test_unknown_kind_dropped(self) -> None:
        raw = {"kind": "keyboard_event"}
        assert normalize_extension_event(raw) is None

    def test_missing_domain_dropped(self) -> None:
        raw = {"kind": "browser_navigation", "url": None}
        assert normalize_extension_event(raw) is None

    def test_tab_close_allows_null_domain(self) -> None:
        raw = {"kind": "browser_tab_close", "tab_id": "7"}
        event = normalize_extension_event(raw)
        assert event is not None
        assert event["browser"]["domain"] is None


class TestBrowserStateStore:
    def test_record_navigation_updates_active_tab(self) -> None:
        store = BrowserStateStore()
        store.record_event(
            {
                "kind": "browser_navigation",
                "device_id": "DEV-1",
                "tab_id": "10",
                "domain": "classroom.google.com",
                "url": "https://classroom.google.com/",
            }
        )
        tabs = store.get_active_tabs("DEV-1")
        assert len(tabs) == 1
        assert tabs[0]["domain"] == "classroom.google.com"
        assert tabs[0]["url"] == "https://classroom.google.com/"

    def test_record_tab_close_does_not_create_active_tab(self) -> None:
        store = BrowserStateStore()
        store.record_event({"kind": "browser_tab_close", "tab_id": "5"})
        assert store.get_active_tabs() == []

    def test_get_active_tabs_returns_all_devices(self) -> None:
        store = BrowserStateStore()
        store.record_event({"kind": "browser_navigation", "device_id": "A", "domain": "a.com"})
        store.record_event({"kind": "browser_navigation", "device_id": "B", "domain": "b.com"})
        assert len(store.get_active_tabs()) == 2

    def test_clear_resets_state(self) -> None:
        store = BrowserStateStore()
        store.record_event({"kind": "browser_navigation", "device_id": "A", "domain": "a.com"})
        store.clear()
        assert store.get_active_tabs() == []


class TestExtensionBrowserMonitor:
    @pytest.mark.asyncio
    async def test_store_mode(self) -> None:
        store = BrowserStateStore()
        store.record_event({"kind": "browser_navigation", "device_id": "DEV-1", "domain": "a.com"})
        monitor = ExtensionBrowserMonitor(store=store, device_id="DEV-1")
        await monitor.start()
        tabs = await monitor.get_active_tabs()
        assert len(tabs) == 1
        assert tabs[0]["domain"] == "a.com"
        await monitor.stop()
        assert monitor.started is False

    @pytest.mark.asyncio
    async def test_http_mode_returns_empty_when_backend_offline(self) -> None:
        monitor = ExtensionBrowserMonitor(api_url="http://127.0.0.1:59999")
        tabs = await monitor.get_active_tabs()
        assert tabs == []