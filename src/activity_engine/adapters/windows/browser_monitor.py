"""Windows browser monitor stub (LEGACY).

[LEGACY] Phase 1 stub — browser extension integration is not yet implemented.

This stub documents the :class:`~activity_engine.ports.BrowserMonitor` contract
and raises :class:`NotImplementedError` on every method so that any accidental
use fails fast rather than silently doing nothing.

The canonical / tested path for browser telemetry is
:class:`~activity_engine.adapters.extension.browser_monitor.ExtensionBrowserMonitor`
(Chrome extension bridge), or :class:`~activity_engine.adapters.mock.browser_monitor.MockBrowserMonitor`
for simulation.
"""

from __future__ import annotations

from typing import Any

class WindowsBrowserMonitor:
    """Stub for Windows browser monitoring via browser extension."""

    def __init__(self) -> None:
        self.started = False

    async def start(self) -> None:
        raise NotImplementedError(
            "WindowsBrowserMonitor not implemented in Phase 1. "
            "Browser extension integration is a future extension point. "
            "Use MockBrowserMonitor for testing."
        )

    async def stop(self) -> None:
        raise NotImplementedError("Not implemented in Phase 1")

    async def get_active_tabs(self) -> list[dict[str, Any]]:
        raise NotImplementedError("Not implemented in Phase 1")