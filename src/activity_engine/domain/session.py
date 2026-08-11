"""Monitoring session domain model."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

class MonitoringSession(BaseModel):
    """A monitoring session for one student on one device."""

    model_config = ConfigDict(frozen=True)

    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    device_id: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    ended_at: datetime | None = None

    @property
    def is_active(self) -> bool:
        return self.ended_at is None

    def end(self) -> "MonitoringSession":
        return self.model_copy(update={"ended_at": datetime.now(UTC)})