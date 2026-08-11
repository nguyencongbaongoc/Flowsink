"""Windows browser monitor stub.

Phase 1: Browser extension integration is not yet implemented. This stub
documents the contract and raises NotImplementedError if used.
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