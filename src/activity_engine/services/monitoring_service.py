"""Monitoring Service — polls monitors and feeds the Event Engine.

Implements graceful fault isolation: if one monitor dies, the others keep
running. Each monitor runs in its own asyncio task.
"""

from __future__ import annotations

import asyncio
from typing import Any

from ..core.errors import MonitorError
from ..engine.event_engine import EventEngine
from ..utils.logging import create_logger

_logger = create_logger()

class MonitoringService:
    """Orchestrates monitor adapters and feeds the Event Engine."""

    def __init__(
        self,
        event_engine: EventEngine,
        monitors: dict[str, Any],
        poll_interval_seconds: float = 3.0,
    ) -> None:
        self._event_engine = event_engine
        self._monitors = monitors
        self._poll_interval_seconds = poll_interval_seconds
        self._tasks: list[asyncio.Task] = []
        self._running = False

    async def start(self) -> None:
        """Start all monitors as isolated tasks."""
        self._running = True
        for name, monitor in self._monitors.items():
            task = asyncio.create_task(self._run_monitor(name, monitor))
            self._tasks.append(task)

    async def stop(self) -> None:
        """Stop all monitors gracefully."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        for task in self._tasks:
            try:
                await task
            except asyncio.CancelledError:
                pass
        self._tasks.clear()

    async def _run_monitor(self, name: str, monitor: Any) -> None:
        """Run one monitor; crashes are contained to this task."""
        try:
            await monitor.start()
        except NotImplementedError as exc:
            _logger.warning("monitor=%s status=unavailable reason=%s", name, exc)
            return
        except Exception as exc:  # noqa: BLE001
            _logger.warning("monitor=%s start_failed error=%s", name, exc)
            return

        _logger.info("monitor=%s status=running", name)
        try:
            if name == "process":
                await self._poll_process(monitor)
            elif name == "browser":
                await self._poll_browser(monitor)
            elif name == "network":
                await self._poll_network(monitor)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - fault isolation
            _logger.warning("monitor=%s crashed error=%s", name, exc)
        finally:
            try:
                await monitor.stop()
            except Exception:  # noqa: BLE001
                pass

    async def _poll_process(self, monitor: Any) -> None:
        last_foreground: tuple[str, int] | None = None
        while self._running:
            try:
                fg = await monitor.get_foreground_process()
                key = None
                if fg and fg.get("process"):
                    key = (str(fg.get("process")), int(fg.get("pid") or 0))
                if key and key != last_foreground:
                    last_foreground = key
                    await self._event_engine.process_raw(
                        {
                            "kind": "process_focus",
                            "application": fg,
                        }
                    )
            except Exception as exc:  # noqa: BLE001
                _logger.warning("monitor=process poll_error error=%s", exc)
            await asyncio.sleep(self._poll_interval_seconds)

    async def _poll_browser(self, monitor: Any) -> None:
        while self._running:
            try:
                tabs = await monitor.get_active_tabs()
                if tabs:
                    tab = tabs[0]
                    await self._event_engine.process_raw(
                        {
                            "kind": "browser_navigation",
                            "browser": {
                                "name": tab.get("name"),
                                "tab_id": tab.get("tab_id"),
                                "domain": tab.get("domain"),
                            },
                        }
                    )
            except Exception as exc:  # noqa: BLE001
                _logger.warning("monitor=browser poll_error error=%s", exc)
            await asyncio.sleep(self._poll_interval_seconds)

    async def _poll_network(self, monitor: Any) -> None:
        while self._running:
            try:
                domains = await monitor.get_recent_domains()
                for entry in domains:
                    if entry.get("domain"):
                        await self._event_engine.process_raw(
                            {
                                "kind": "dns_request",
                                "network": {
                                    "domain": entry.get("domain"),
                                    "protocol": entry.get("protocol"),
                                },
                            }
                        )
            except Exception as exc:  # noqa: BLE001
                _logger.warning("monitor=network poll_error error=%s", exc)
            await asyncio.sleep(self._poll_interval_seconds * 2)