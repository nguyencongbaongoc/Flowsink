"""Mock process monitor for tests and simulation."""

from __future__ import annotations

from typing import Any

class MockProcessMonitor:
    """Configurable fake of the ProcessMonitor port."""

    def __init__(self, foreground: dict[str, Any] | None = None) -> None:
        self._foreground = foreground
        self._running: list[dict[str, Any]] = []
        self.started = False

    async def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.started = False

    async def get_running_processes(self) -> list[dict[str, Any]]:
        return list(self._running)

    async def get_foreground_process(self) -> dict[str, Any] | None:
        return self._foreground

    def set_foreground(self, name: str, process: str, pid: int = 1234) -> None:
        self._foreground = {"name": name, "process": process, "pid": pid}

    def add_process(self, name: str, process: str, pid: int) -> None:
        self._running.append({"name": name, "process": process, "pid": pid})