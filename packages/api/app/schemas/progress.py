"""Schemas for real-time progress events."""

from datetime import datetime, timezone
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

ProgressStatus = Literal["queued", "rendering", "done", "failed", "phase_update"]


class ProgressEvent(BaseModel):
    job_id: UUID
    brief_id: UUID
    status: ProgressStatus
    phase: str | None = None
    progress_pct: int | None = Field(default=None, ge=0, le=100)
    message: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def to_channel(self) -> str:
        return f"progress:brief:{self.brief_id}"

    def to_json(self) -> str:
        return self.model_dump_json()
