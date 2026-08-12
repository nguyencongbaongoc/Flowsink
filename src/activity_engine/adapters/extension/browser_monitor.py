"""BrowserMonitor adapter backed by the Chrome extension telemetry bridge.

Two consumption modes:

1. **Shared store (in-process)** — when the backend server and the monitoring
   loop run in the same process, the server's ``BrowserStateStore`` is read
   directly.

2. **HTTP polling (cross-process)** — when the CLI monitor runs separately
   from the FastAPI backend (normal Windows setup), the adapter polls
   ``GET {api_base_url}/api/browser/active`` to fetch the latest active tabs.

The adapter implements the ``BrowserMonitor`` port so the existing
``MonitoringService`` browser poll loop feeds the EventEngine:

    Browser Extension -> Backend -> BrowserStateStore
    -> ExtensionBrowserMonitor -> MonitoringService -> EventEngine
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any
from urllib.request import urlopen

from ...services.browser_state import BrowserStateStore

logger = logging.getLogger(__name__)

class ExtensionBrowserMonitor:
    """BrowserMonitor port implementation for Chrome extension telemetry."""

    def __init__(
        self,
        store: BrowserStateStore | None = None,
        device_id: str | None = None,
        api_url: str | None = None,
    ) -> None:
        """Construct the adapter.

        Args:
            store: Shared store for in-process mode. A fresh store is created
                when not provided (and no ``api_url`` is set).
            device_id: Filter active tabs to one device (in-process mode only).
            api_url: Backend base URL (e.g. ``http://127.0.0.1:8000``). When
                set, the adapter polls the backend instead of the shared store.
        """
        self._store = store or BrowserStateStore()
        self._device_id = device_id
        self._api_url = api_url.rstrip("/") if api_url else None
        self.started = False

    @property
    def store(self) -> BrowserStateStore:
        """Expose the underlying store (used by the server bridge)."""
        return self._store

    async def start(self) -> None:
        """Start the monitor. Stateless — nothing to prepare."""
        self.started = True

    async def stop(self) -> None:
        """Stop the monitor."""
        self.started = False

    async def get_active_tabs(self) -> list[dict[str, Any]]:
        """Return the latest active tab(s) tracked by the extension bridge."""
        if self._api_url:
            return await self._poll_http()
        return self._store.get_active_tabs(self._device_id)

    async def _poll_http(self) -> list[dict[str, Any]]:
        """Poll the backend's active-tab endpoint."""
        url = f"{self._api_url}/api/browser/active"
        try:
            data = await asyncio.to_thread(self._http_get, url)
            if data is None:
                return []
            tabs = data.get("tabs") or []
            return [tab for tab in tabs if isinstance(tab, dict)]
        except Exception as exc:  # noqa: BLE001 - polling must never crash
            logger.warning("browser_monitor=poll_http_failed error=%s", exc)
            return []

    @staticmethod
    def _http_get(url: str) -> dict[str, Any] | None:
        """Synchronous HTTP GET used via asyncio.to_thread."""
        try:
            with urlopen(url, timeout=3) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                parsed = json.loads(body)
                return parsed if isinstance(parsed, dict) else None
        except Exception:  # noqa: BLE001 - backend may be offline
            return None