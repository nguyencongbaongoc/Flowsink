"""Windows network/DNS monitor stub.

Phase 1: WinDivert / Raw socket packet interception is not yet implemented.
This stub documents the contract and raises NotImplementedError if used.
"""

from __future__ import annotations

from typing import Any

class WindowsNetworkMonitor:
    """Stub for Windows network monitoring via WinDivert or raw sockets."""

    def __init__(self) -> None:
        self.started = False

    async def start(self) -> None:
        raise NotImplementedError(
            "WindowsNetworkMonitor not implemented in Phase 1. "
            "Raw packet/DNS telemetry is a future extension point. "
            "Use MockNetworkMonitor for testing."
        )

    async def stop(self) -> None:
        raise NotImplementedError("Not implemented in Phase 1")

    async def get_recent_domains(self) -> list[dict[str, Any]]:
        raise NotImplementedError("Not implemented in Phase 1")