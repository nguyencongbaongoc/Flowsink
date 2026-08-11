"""Enforcement action model.

All enforcement actions flow through :class:`ActionRequest` objects handled by
an ``ActionExecutor`` adapter. Every action is idempotent: repeating the same
request (same target, same action within an active period) does not create
repeated system mutations.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

class ActionType(StrEnum):
    """Typed actions exposed to the outside world.

    Deliberately no ``execute_shell`` or arbitrary command execution. Remote
    control is limited to these typed actions.
    """

    WARN = "WARN"
    REDIRECT = "REDIRECT"
    CLOSE_APPLICATION = "CLOSE_APPLICATION"
    BLOCK_DOMAIN = "BLOCK_DOMAIN"
    ENABLE_RESTRICTED_MODE = "ENABLE_RESTRICTED_MODE"
    DISABLE_RESTRICTED_MODE = "DISABLE_RESTRICTED_MODE"

class ActionStatus(StrEnum):
    """Result status of an executed action."""

    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"  # Idempotent duplicate — no system mutation performed
    NOT_EXECUTED = "NOT_EXECUTED"  # Dry-run / audit-only

class WarningRequest(BaseModel):
    """Level 1 — issue a warning message to the student."""

    model_config = ConfigDict(frozen=True)

    student_id: str
    message: str = "Bạn đang truy cập nội dung ngoài nhiệm vụ. Vui lòng quay lại website được phép."
    policy_id: str = "focus-default"
    reason: str = "FOCUS_POLICY"

class RedirectRequest(BaseModel):
    """Level 2 — redirect the browser to an allowed website."""

    model_config = ConfigDict(frozen=True)

    student_id: str
    target_domain: str
    allowed_url: str = "https://classroom.google.com/"
    policy_id: str = "focus-default"
    reason: str = "FOCUS_POLICY"

class CloseApplicationRequest(BaseModel):
    """Level 2 — close a disallowed application."""

    model_config = ConfigDict(frozen=True)

    student_id: str
    application: str
    process: str | None = None
    policy_id: str = "focus-default"
    reason: str = "FOCUS_POLICY"

class BlockDomainRequest(BaseModel):
    """Level 2 — block a domain via a local hosts entry or DNS mechanism."""

    model_config = ConfigDict(frozen=True)

    student_id: str
    domain: str
    policy_id: str = "focus-default"
    reason: str = "FOCUS_POLICY"

class RestrictedModeRequest(BaseModel):
    """Level 3 — switch the device into protected/restricted mode."""

    model_config = ConfigDict(frozen=True)

    student_id: str
    mode_name: str = "RESTRICTED"
    policy_id: str = "focus-default"
    reason: str = "FOCUS_POLICY_REPEATED_VIOLATION"

class EnableRestrictedModeRequest(RestrictedModeRequest):
    """Level 3 — enable protected/restricted mode."""

    reason: str = "ENABLE_RESTRICTED_MODE"

class DisableRestrictedModeRequest(RestrictedModeRequest):
    """Turn restricted mode back off."""

    reason: str = "DISABLE_RESTRICTED_MODE"

class ActionRequest(BaseModel):
    """Generic envelope carrying any typed action request."""

    model_config = ConfigDict(frozen=True)

    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action: ActionType
    target: str = ""
    policy_id: str = "focus-default"
    reason: str = ""
    student_id: str = ""
    issued_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    payload: WarningRequest | RedirectRequest | CloseApplicationRequest | BlockDomainRequest | RestrictedModeRequest | None = None

class ActionResult(BaseModel):
    """Result of executing an action."""

    model_config = ConfigDict(frozen=True)

    action_id: str
    action: ActionType
    target: str
    policy_id: str
    reason: str
    student_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    status: ActionStatus
    error_code: str | None = None
    error_message: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.status == ActionStatus.SUCCESS