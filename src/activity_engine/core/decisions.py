"""Policy decision model.

The Policy Engine evaluates an :class:`ActivityEvent` and returns a
:class:`PolicyDecision` describing the outcome (allowed, warning, blocked,
etc.) together with the escalation level and the action plan the Action Engine
should execute.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .actions import ActionType
from .policies import EnforcementLevel

class EnforcementMode(StrEnum):
    """Runtime enforcement mode (mirrors ActionMode for decision purposes)."""

    DRY_RUN = "dry_run"
    AUDIT_ONLY = "audit_only"
    ENFORCE = "enforce"

class PolicyOutcome(StrEnum):
    """Categorical result of a policy evaluation."""

    ALLOWED = "ALLOWED"
    FOCUS = "FOCUS"
    WARNING = "WARNING"
    OFF_TASK = "OFF_TASK"
    BLOCKED = "BLOCKED"
    RESTRICT = "RESTRICT"
    BEDTIME = "BEDTIME"
    POTENTIAL_ACTIVITY = "POTENTIAL_ACTIVITY"
    IGNORED = "IGNORED"

class PolicyDecision(BaseModel):
    """The result of evaluating one event against the active policy."""

    model_config = ConfigDict(frozen=True)

    event_id: str
    student_id: str | None = None
    policy_id: str = "focus-default"
    outcome: PolicyOutcome
    level: EnforcementLevel | None = None
    action_types: list[ActionType] = Field(default_factory=list)
    reason: str = ""
    targets: list[str] = Field(default_factory=list)
    domain: str | None = None
    application: str | None = None
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)