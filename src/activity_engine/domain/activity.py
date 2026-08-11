"""Activity domain model — an aggregate view of what the student is doing."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field

from ..core.events import ApplicationInfo, BrowserInfo

class CurrentActivity(BaseModel):
    """Represents the student's current observable activity."""

    model_config = ConfigDict(frozen=True)

    student_id: str
    device_id: str
    application: ApplicationInfo = Field(default_factory=ApplicationInfo)
    browser: BrowserInfo = Field(default_factory=BrowserInfo)
    since: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_seen: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_browser: bool = False
    is_allowed: bool = True

    @property
    def primary_label(self) -> str:
        """Human readable label of the current activity."""
        if self.browser.domain:
            return self.browser.domain
        if self.application.name:
            return self.application.name
        if self.application.process:
            return self.application.process
        return "<unknown>"

    def duration_seconds(self, now: datetime | None = None) -> float:
        """Elapsed seconds since this activity started."""
        reference = now or datetime.now(UTC)
        return max(0.0, (reference - self.since).total_seconds())