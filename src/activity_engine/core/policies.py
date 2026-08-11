"""Policy model.

Policies are fully configurable documents. No policy decision is hard-coded in
the monitors or engines; all decisions flow through the Policy Engine which
evaluates :class:`ActivityEvent` objects against a :class:`PolicyDocument`.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EnforcementLevel(StrEnum):
    """Escalation levels."""

    LEVEL_1 = "level_1"
    LEVEL_2 = "level_2"
    LEVEL_3 = "level_3"


class ActionMode(StrEnum):
    """Runtime enforcement mode.

    - ``dry_run``: record what *would* happen; never enforce.
    - ``audit_only``: like dry-run but also writes detailed audit records.
    - ``enforce``: execute real enforcement actions.
    """

    DRY_RUN = "dry_run"
    AUDIT_ONLY = "audit_only"
    ENFORCE = "enforce"


class BedtimeStage(StrEnum):
    """Stages of the bedtime flow."""

    NONE = "none"
    LEVEL_1 = "level_1"
    LEVEL_2 = "level_2"
    LEVEL_3 = "level_3"


class FocusPolicy(BaseModel):
    """Focus-mode policy: which domains/apps are allowed or blocked."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = True
    allowed_domains: list[str] = Field(default_factory=list)
    blocked_domains: list[str] = Field(default_factory=list)
    allowed_apps: list[str] = Field(default_factory=list)
    blocked_apps: list[str] = Field(default_factory=list)
    allowed_url_patterns: list[str] = Field(default_factory=list)
    escalation_delay_seconds: int = Field(default=10, ge=0)
    violation_threshold: int = Field(default=3, ge=1)


class EscalationPolicy(BaseModel):
    """Three-level escalation settings for focus violations."""

    model_config = ConfigDict(frozen=True)

    level_1_delay_seconds: int = Field(default=10, ge=0)
    level_2_delay_seconds: int = Field(default=30, ge=0)
    level_3_violation_threshold: int = Field(default=3, ge=1)


class BedtimePolicy(BaseModel):
    """Bedtime schedule and warnings."""

    model_config = ConfigDict(frozen=True)

    enabled: bool = False
    start_time: str = "22:30"
    level_1_warning_minutes: int = Field(default=15, ge=0)
    level_2_warning_minutes: int = Field(default=5, ge=0)
    level_3_action: Literal["restricted_mode", "shutdown", "lock"] = "restricted_mode"

    @field_validator("start_time")
    @classmethod
    def validate_time_format(cls, value: str) -> str:
        """Validate HH:MM 24-hour format."""
        try:
            hour, minute = value.split(":")
            h, m = int(hour), int(minute)
            if not (0 <= h <= 23 and 0 <= m <= 59):
                raise ValueError
        except (ValueError, AttributeError) as exc:
            raise ValueError(f"Invalid start_time: {value!r}. Expected 'HH:MM'.") from exc
        return f"{h:02d}:{m:02d}"


class PolicyDocument(BaseModel):
    """A complete, validated set of policies."""

    model_config = ConfigDict(frozen=True)

    version: str = "1"
    focus: FocusPolicy = Field(default_factory=FocusPolicy)
    bedtime: BedtimePolicy = Field(default_factory=BedtimePolicy)
    escalation: EscalationPolicy = Field(default_factory=EscalationPolicy)