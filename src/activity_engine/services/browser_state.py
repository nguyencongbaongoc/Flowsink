"""Browser state store — active tab tracking for the browser extension bridge.

The Chrome extension pushes tab telemetry to ``POST /api/browser/telemetry``.
This store records the most recent active tab per device so the
``ExtensionBrowserMonitor`` adapter can poll ``GET /api/browser/active`` and
the ``MonitoringService`` browser loop can feed the EventEngine.

The store is bounded (max 64 entries) and intentionally small: it only tracks
the fields the policy engine consumes.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from ..logging import get_logger
from .browser_events import normalize_extension_event

logger = get_logger("activity_engine.services.browser_state", component="BROWSER", event="STATE")

_MAX_DEVICES = 64

class BrowserStateStore:
    """Keeps the latest active tab per device."""

    def __init__(self) -> None:
        self._active: dict[str, dict[str, Any]] = {}
        self._devices: list[str] = []

    def record_event(self, raw: dict[str, Any]) -> dict[str, Any] | None:
        """Normalize an extension payload and update the active tab state.

        Returns the normalized raw event (ready for ``engine.feed_raw``) or
        ``None`` when the payload was dropped by validation.
        """
        event = normalize_extension_event(raw)
        if event is None:
            return None

        browser = event["browser"]
        logger.debug(
            "kind=%s device=%s",
            event["kind"],
            (event.get("metadata") or {}).get("extension_device_id") or "unknown-device",
            event="RECORDED",
            component="BROWSER",
        )
        device_key = (
            str((event.get("metadata") or {}).get("extension_device_id") or "")
            or "unknown-device"
        )
        domain = browser.get("domain")
        tab_id = browser.get("tab_id")

        # Only navigation/focus events update the active tab.
        if event["kind"] in ("browser_navigation", "browser_tab_focus") and domain:
            snapshot = {
                "name": browser.get("name") or "chrome",
                "tab_id": tab_id,
                "domain": domain,
                "url": browser.get("url"),
                "title": browser.get("title"),
                "updated_at": datetime.now(UTC).isoformat(),
            }
            if device_key not in self._active:
                self._devices.append(device_key)
                if len(self._devices) > _MAX_DEVICES:
                    oldest = self._devices.pop(0)
                    self._active.pop(oldest, None)
            self._active[device_key] = snapshot

        return event

    def get_active_tabs(self, device_id: str | None = None) -> list[dict[str, Any]]:
        """Return the latest active tab per device (or one device)."""
        if device_id:
            tab = self._active.get(device_id)
            return [dict(tab)] if tab else []
        return [dict(tab) for tab in self._active.values()]

    def clear(self) -> None:
        self._active.clear()
        self._devices.clear()