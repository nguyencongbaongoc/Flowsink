"""Activity Service — tracks current activity and exposes it to callers."""

from __future__ import annotations

from ..core.decisions import PolicyDecision
from ..core.events import ActivityEvent
from ..engine.state_engine import StateEngine
from ..domain.activity import CurrentActivity

class ActivityService:
    """Maintains the current activity aggregate for a student."""

    def __init__(self, student_id: str, device_id: str, state_engine: StateEngine) -> None:
        self._student_id = student_id
        self._device_id = device_id
        self._state_engine = state_engine
        self._current: CurrentActivity | None = None

    def update_from_event(self, event: ActivityEvent) -> CurrentActivity:
        """Update the current activity from a canonical event."""
        self._current = CurrentActivity(
            student_id=event.student_id or self._student_id,
            device_id=event.device_id,
            application=event.application,
            browser=event.browser,
            last_seen=event.timestamp,
            is_browser=event.source.value == "browser",
        )
        return self._current

    @property
    def current(self) -> CurrentActivity | None:
        return self._current

    def reset(self) -> None:
        self._current = None