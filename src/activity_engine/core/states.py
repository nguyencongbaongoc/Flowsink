"""Activity state model.

The engine keeps a single, explicit state machine for each monitored student.
This avoids the boolean explosion pattern (``is_bad`` / ``is_warning`` /
``is_blocked`` / ...) that leads to invalid combinations.
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class ActivityState(StrEnum):
    """Explicit, mutually-exclusive states of the state machine."""

    UNKNOWN = "UNKNOWN"
    FOCUS = "FOCUS"
    ALLOWED = "ALLOWED"
    WARNING = "WARNING"
    OFF_TASK = "OFF_TASK"
    BLOCKED = "BLOCKED"
    RESTRICTED = "RESTRICTED"
    BEDTIME = "BEDTIME"


# Valid transitions between states. ``None`` keys are not present; the state
# machine only allows transitions listed below. Any other transition raises an
# ``InvalidStateTransition`` error.
_VALID_TRANSITIONS: dict[ActivityState, frozenset[ActivityState]] = {
    ActivityState.UNKNOWN: frozenset(
        {
            ActivityState.FOCUS,
            ActivityState.ALLOWED,
            ActivityState.WARNING,
            ActivityState.OFF_TASK,
            ActivityState.BLOCKED,
            ActivityState.RESTRICTED,
            ActivityState.BEDTIME,
        }
    ),
    ActivityState.FOCUS: frozenset(
        {
            ActivityState.ALLOWED,
            ActivityState.WARNING,
            ActivityState.OFF_TASK,
            ActivityState.BLOCKED,
            ActivityState.RESTRICTED,
            ActivityState.BEDTIME,
        }
    ),
    ActivityState.ALLOWED: frozenset(
        {
            ActivityState.FOCUS,
            ActivityState.WARNING,
            ActivityState.OFF_TASK,
            ActivityState.BLOCKED,
            ActivityState.RESTRICTED,
            ActivityState.BEDTIME,
        }
    ),
    ActivityState.WARNING: frozenset(
        {
            ActivityState.FOCUS,
            ActivityState.ALLOWED,
            ActivityState.OFF_TASK,
            ActivityState.BLOCKED,
            ActivityState.RESTRICTED,
            ActivityState.BEDTIME,
        }
    ),
    ActivityState.OFF_TASK: frozenset(
        {
            ActivityState.FOCUS,
            ActivityState.ALLOWED,
            ActivityState.WARNING,
            ActivityState.BLOCKED,
            ActivityState.RESTRICTED,
            ActivityState.BEDTIME,
        }
    ),
    ActivityState.BLOCKED: frozenset(
        {
            ActivityState.FOCUS,
            ActivityState.ALLOWED,
            ActivityState.WARNING,
            ActivityState.OFF_TASK,
            ActivityState.RESTRICTED,
            ActivityState.BEDTIME,
        }
    ),
    ActivityState.RESTRICTED: frozenset(
        {
            ActivityState.FOCUS,
            ActivityState.ALLOWED,
            ActivityState.BEDTIME,
        }
    ),
    ActivityState.BEDTIME: frozenset(
        {
            ActivityState.FOCUS,
            ActivityState.ALLOWED,
            ActivityState.RESTRICTED,
        }
    ),
}


class StateSnapshot(BaseModel):
    """Current observable state of a student on a device."""

    model_config = ConfigDict(frozen=True)

    student_id: str
    device_id: str
    state: ActivityState = ActivityState.UNKNOWN
    application: str | None = Field(default=None, description="Application/process currently foreground")
    domain: str | None = Field(default=None, description="Domain currently active in browser (if known)")
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    duration_seconds: float = 0.0
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    session_id: str | None = None
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class InvalidStateTransition(Exception):
    """Raised when the state machine receives an illegal transition."""

    def __init__(self, current: ActivityState, target: ActivityState) -> None:
        super().__init__(f"Invalid state transition: {current.value} -> {target.value}")
        self.current = current
        self.target = target


class ActivityStateMachine:
    """Small, explicit state machine guarding activity states."""

    def __init__(self, initial: ActivityState = ActivityState.UNKNOWN) -> None:
        self._state = initial

    @property
    def state(self) -> ActivityState:
        return self._state

    def can_transition(self, target: ActivityState) -> bool:
        return target in _VALID_TRANSITIONS.get(self._state, frozenset())

    def transition(self, target: ActivityState) -> ActivityState:
        """Transition to ``target``. Raises :class:`InvalidStateTransition` if illegal."""
        if target == self._state:
            return self._state
        allowed = _VALID_TRANSITIONS.get(self._state, frozenset())
        if target not in allowed:
            raise InvalidStateTransition(self._state, target)
        self._state = target
        return self._state

    def reset(self) -> None:
        self._state = ActivityState.UNKNOWN