from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.brief import CreativeBrief


class RenderJob(BaseModel):
    __tablename__ = "render_jobs"

    brief_id: Mapped[UUID] = mapped_column(
        ForeignKey("creative_briefs.id"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(50), server_default="queued")
    composition: Mapped[dict | None] = mapped_column(JSONB)
    output_s3_key: Mapped[str | None] = mapped_column(String(500))
    render_duration_ms: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    celery_task_id: Mapped[str | None] = mapped_column(String(255))

    brief: Mapped[CreativeBrief] = relationship(back_populates="render_jobs")

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "queued")
        super().__init__(**kwargs)
