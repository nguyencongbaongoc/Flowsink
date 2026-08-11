"""Event Engine — validation, normalization, deduplication, ordering.

Pipeline:
    Raw Event -> Validation -> Normalization -> Deduplication
    -> Ordering -> State Update -> Policy Evaluation

The Event Engine is fault-isolated: a malformed event is dropped and counted,
never raised to crash the agent.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Callable

from pydantic import ValidationError

from ..core.events import ActivityEvent
from ..utils.logging import create_logger

_logger = create_logger()


class EventInput(StrEnum):
    """Accepted raw event shapes from adapters."""

    PROCESS_FOCUS = "process_focus"
    PROCESS_START = "process_start"
    PROCESS_STOP = "process_stop"
    BROWSER_NAVIGATION = "browser_navigation"
    BROWSER_TAB_FOCUS = "browser_tab_focus"
    BROWSER_TAB_CLOSE = "browser_tab_close"
    DNS_REQUEST = "dns_request"
    USER_IDLE = "user_idle"
    USER_ACTIVE = "user_active"


class EventEngine:
    """Normalizes raw telemetry into versioned :class:`ActivityEvent` objects."""

    def __init__(
        self,
        device_id: str,
        student_id: str | None = None,
        debounce_seconds: float = 1.0,
        max_stale_seconds: float = 120.0,
    ) -> None:
        self._device_id = device_id
        self._student_id = student_id
        self._debounce_seconds = debounce_seconds
        self._max_stale_seconds = max_stale_seconds
        self._last_seen: dict[str, float] = {}
        self._subscribers: list[Callable[[ActivityEvent], Any]] = []
        self.metrics = {
            "events_received": 0,
            "events_processed": 0,
            "events_dropped": 0,
            "events_duplicate": 0,
            "events_stale": 0,
        }

    # ------------------------------------------------------------------
    # Subscribers
    # ------------------------------------------------------------------
    def subscribe(self, callback: Callable[[ActivityEvent], Any]) -> None:
        """Register a callback invoked for every processed event."""
        self._subscribers.append(callback)

    async def _notify(self, event: ActivityEvent) -> None:
        for callback in self._subscribers:
            try:
                result = callback(event)
                if hasattr(result, "__await__"):
                    await result
            except Exception:  # noqa: BLE001 - subscriber errors must not crash engine
                _logger.warning("event=subscriber_error event_id=%s", event.event_id)

    # ------------------------------------------------------------------
    # Public pipeline
    # ------------------------------------------------------------------
    async def process_raw(self, raw: dict[str, Any]) -> ActivityEvent | None:
        """Process a raw telemetry dict. Returns the normalized event or None."""
        self.metrics["events_received"] += 1
        try:
            event = self.normalize(raw)
        except (ValidationError, ValueError) as exc:
            self.metrics["events_dropped"] += 1
            _logger.warning("event=drop reason=validation error=%s", exc)
            return None

        if self._is_stale(event):
            self.metrics["events_stale"] += 1
            self.metrics["events_dropped"] += 1
            _logger.warning("event=drop reason=stale event_id=%s", event.event_id)
            return None

        if self._is_duplicate(event):
            self.metrics["events_duplicate"] += 1
            self.metrics["events_dropped"] += 1
            return None

        self.metrics["events_processed"] += 1
        await self._notify(event)
        return event

    async def process(self, event: ActivityEvent) -> ActivityEvent:
        """Accept an already-normalized event (e.g. from a service)."""
        if self._is_stale(event):
            self.metrics["events_stale"] += 1
            self.metrics["events_dropped"] += 1
            return event
        if self._is_duplicate(event):
            self.metrics["events_duplicate"] += 1
        self.metrics["events_processed"] += 1
        await self._notify(event)
        return event

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------
    def normalize(self, raw: dict[str, Any]) -> ActivityEvent:
        """Normalize a raw adapter dict into a canonical event."""
        kind = raw.get("kind") or raw.get("type")
        timestamp = raw.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        elif timestamp is None:
            timestamp = datetime.now(UTC)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)

        base = dict(raw)
        base.pop("kind", None)
        base.pop("type", None)

        if kind in (EventInput.PROCESS_FOCUS, EventInput.PROCESS_START, EventInput.PROCESS_STOP):
            return self._normalize_process(raw, timestamp, kind)
        if kind in (EventInput.BROWSER_NAVIGATION, EventInput.BROWSER_TAB_FOCUS, EventInput.BROWSER_TAB_CLOSE):
            return self._normalize_browser(raw, timestamp, kind)
        if kind == EventInput.DNS_REQUEST:
            return self._normalize_dns(raw, timestamp)
        if kind in (EventInput.USER_IDLE, EventInput.USER_ACTIVE):
            return self._normalize_user_presence(raw, timestamp, kind)
        raise ValueError(f"Unknown raw event kind: {kind!r}")

    def _normalize_process(
        self, raw: dict[str, Any], timestamp: datetime, kind: str
    ) -> ActivityEvent:
        app = raw.get("application", {})
        event_type = {
            EventInput.PROCESS_FOCUS: "APP_FOCUSED",
            EventInput.PROCESS_START: "APP_STARTED",
            EventInput.PROCESS_STOP: "APP_CLOSED",
        }[kind]
        return ActivityEvent(
            device_id=self._device_id,
            student_id=self._student_id,
            timestamp=timestamp,
            source="process",
            type=event_type,
            application={
                "name": app.get("name"),
                "process": app.get("process"),
                "pid": app.get("pid"),
                "window_title": app.get("window_title"),
            },
            metadata=raw.get("metadata") or {},
        )

    def _normalize_browser(
        self, raw: dict[str, Any], timestamp: datetime, kind: str
    ) -> ActivityEvent:
        browser = raw.get("browser", {})
        event_type = {
            EventInput.BROWSER_NAVIGATION: "WEB_NAVIGATION",
            EventInput.BROWSER_TAB_FOCUS: "WEB_TAB_FOCUSED",
            EventInput.BROWSER_TAB_CLOSE: "WEB_TAB_CLOSED",
        }[kind]
        return ActivityEvent(
            device_id=self._device_id,
            student_id=self._student_id,
            timestamp=timestamp,
            source="browser",
            type=event_type,
            browser={
                "name": browser.get("name"),
                "tab_id": browser.get("tab_id") and str(browser.get("tab_id")),
                "domain": browser.get("domain"),
                "url": browser.get("url"),
                "title": browser.get("title"),
            },
            application={
                "name": browser.get("name"),
            },
            metadata=raw.get("metadata") or {},
        )

    def _normalize_dns(self, raw: dict[str, Any], timestamp: datetime) -> ActivityEvent:
        network = raw.get("network", {})
        return ActivityEvent(
            device_id=self._device_id,
            student_id=self._student_id,
            timestamp=timestamp,
            source="network",
            type="DNS_REQUEST",
            network={"domain": network.get("domain"), "protocol": network.get("protocol", "dns")},
            metadata=raw.get("metadata") or {},
        )

    def _normalize_user_presence(
        self, raw: dict[str, Any], timestamp: datetime, kind: str
    ) -> ActivityEvent:
        return ActivityEvent(
            device_id=self._device_id,
            student_id=self._student_id,
            timestamp=timestamp,
            source="system",
            type="USER_ACTIVE" if kind == EventInput.USER_ACTIVE else "USER_IDLE",
            metadata=raw.get("metadata") or {},
        )

    # ------------------------------------------------------------------
    # Deduplication / ordering
    # ------------------------------------------------------------------
    def _is_duplicate(self, event: ActivityEvent) -> bool:
        key = event.dedupe_key()
        now = event.timestamp.timestamp()
        last = self._last_seen.get(key)
        if last is not None and (now - last) < self._debounce_seconds:
            return True
        self._last_seen[key] = now
        # Prune old keys to avoid unbounded growth.
        if len(self._last_seen) > 4096:
            cutoff = time.time() - 3600
            self._last_seen = {k: v for k, v in self._last_seen.items() if v >= cutoff}
        return False

    def _is_stale(self, event: ActivityEvent) -> bool:
        age = (datetime.now(UTC) - event.timestamp).total_seconds()
        return age > self._max_stale_seconds or age < -self._max_stale_seconds