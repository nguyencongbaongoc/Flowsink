"""Mock network/DNS monitor for tests and simulation."""

from __future__ import annotations

from typing import Any

class MockNetworkMonitor:
    """Configurable fake of the NetworkMonitor port."""

    def __init__(self) -> None:
        self._domains: list[str] = []
        self.started = False

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.started = False

    async def get_recent_domains(self) -> list[dict[str, Any]]:
        return [{"domain": d, "protocol": "dns"} for d in self._domains]

    def add_domain(self, domain: str) -> None:
        self._domains.append(domain)