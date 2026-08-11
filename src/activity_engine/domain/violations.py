"""Violation domain model — audit trail of policy breaches."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from ..core.actions import ActionType
from ..core.states import ActivityState

class ViolationRecord(BaseModel):
    """A single policy violation with audit context."""

    model_config = ConfigDict(frozen=True)

    violation_id: str
    student_id: str
    device_id: str
    session_id: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    state_before: ActivityState
    state_after: ActivityState
    domain: str | None = None
    application: str | None = None
    policy_id: str
    level: str
    action_types: list[ActionType]
    reason: str
    risk_score: float