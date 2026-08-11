"""In-memory repository for events, state, violations.

Phase 1 uses in-memory storage. Future extensions can implement SQLite,
PostgreSQL, or Redis without changing the core.
"""

from __future__ import annotations

from typing import Protocol

from ..core.events import ActivityEvent
from ..core.states import StateSnapshot
from ..domain.violations import ViolationRecord

class ActivityRepository(Protocol):
    """Repository port for persistence."""

    async def store_event(self, event: ActivityEvent) -> None: ...
    async def store_state(self, snapshot: StateSnapshot) -> None: ...
    async def store_violation(self, violation: ViolationRecord) -> None: ...
    async def get_events(self, limit: int = 100) -> list[ActivityEvent]: ...
    async def get_state(self, student_id: str, device_id: str) -> StateSnapshot | None: ...
    async def get_violations(self, student_id: str, limit: int = 100) -> list[ViolationRecord]: ...

class InMemoryActivityRepository:
    """In-memory implementation of ActivityRepository."""

    def __init__(self) -> None:
        self._events: list[ActivityEvent] = []
        self._states: dict[tuple[str, str], StateSnapshot] = {}
        self._violations: list[ViolationRecord] = []

    async def store_event(self, event: ActivityEvent) -> None:
        self._events.append(event)
        if len(self._events) > 1000:
            self._events = self._events[-1000:]

    async def store_state(self, snapshot: StateSnapshot) -> None:
        key = (snapshot.student_id, snapshot.device_id)
        self._states[key] = snapshot

    async def store_violation(self, violation: ViolationRecord) -> None:
        self._violations.append(violation)
        if len(self._violations) > 1000:
            self._violations = self._violations[-1000:]

    async def get_events(self, limit: int = 100) -> list[ActivityEvent]:
        return list(reversed(self._events[-limit:]))

    async def get_state(self, student_id: str, device_id: str) -> StateSnapshot | None:
        return self._states.get((student_id, device_id))

    async def get_violations(self, student_id: str, limit: int = 100) -> list[ViolationRecord]:
        return [v for v in reversed(self._violations) if v.student_id == student_id][:limit]