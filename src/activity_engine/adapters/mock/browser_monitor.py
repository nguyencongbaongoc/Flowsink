"""Mock browser monitor for tests and simulation."""

from __future__ import annotations

from typing import Any

class MockBrowserMonitor:
    """Configurable fake of the BrowserMonitor port."""

    def __init__(self) -> None:
        self._tabs: list[dict[str, Any]] = []
        self.started = False
        self.events: list[dict[str, Any]] = []

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.started = False

    async def get_active_tabs(self) -> list[dict[str, Any]]:
        return list(self._tabs)

    def set_active_tab(self, domain: str, name: str = "chrome", tab_id: str = "tab-1") -> None:
        self._tabs = [{"name": name, "tab_id": tab_id, "domain": domain}]

    def emit(self, kind: str, domain: str, **kwargs: Any) -> None:
        """Record a raw browser event for later replay into the engine."""
        event: dict[str, Any] = {"kind": kind, "browser": {"name": kwargs.pop("name", "chrome"), "domain": domain}}
        event["browser"].update(kwargs)
        self.events.append(event)