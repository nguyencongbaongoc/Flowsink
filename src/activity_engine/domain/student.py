"""Student domain model."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

class Student(BaseModel):
    """A monitored student."""

    model_config = ConfigDict(frozen=True)

    student_id: str
    display_name: str | None = None
    grade: str | None = None
    device_id: str | None = None