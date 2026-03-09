from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.composition import Composition

JobStatus = Literal["queued", "rendering", "done", "failed"]


class JobCreate(BaseModel):
    brief_id: UUID
    status: JobStatus = "queued"
    composition: Composition | None = None


class JobRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    brief_id: UUID
    status: str
    composition: dict | None
    output_s3_key: str | None
    render_duration_ms: int | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime | None


class JobUpdate(BaseModel):
    status: JobStatus | None = None
    composition: Composition | None = None
    output_s3_key: str | None = None
    render_duration_ms: int | None = None
    error_message: str | None = None
