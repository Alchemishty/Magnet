from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.job import RenderJob
    from app.models.project import Project


class CreativeBrief(BaseModel):
    __tablename__ = "creative_briefs"

    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id"), nullable=False, index=True
    )
    hook_type: Mapped[str | None] = mapped_column(String(100))
    narrative_angle: Mapped[str | None] = mapped_column(String(255))
    script: Mapped[str | None] = mapped_column(Text)
    voiceover_text: Mapped[str | None] = mapped_column(Text)
    target_emotion: Mapped[str | None] = mapped_column(String(100))
    cta_text: Mapped[str | None] = mapped_column(String(255))
    reference_ads: Mapped[list] = mapped_column(
        JSONB, server_default="[]"
    )
    target_format: Mapped[str] = mapped_column(
        String(20), server_default="9:16"
    )
    target_duration: Mapped[int] = mapped_column(
        Integer, server_default="15"
    )
    status: Mapped[str] = mapped_column(
        String(50), server_default="draft"
    )
    generated_by: Mapped[str] = mapped_column(
        String(50), server_default="agent"
    )
    scene_plan: Mapped[dict | None] = mapped_column(JSONB)

    project: Mapped[Project] = relationship(
        back_populates="briefs"
    )
    render_jobs: Mapped[list[RenderJob]] = relationship(
        back_populates="brief"
    )

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "draft")
        kwargs.setdefault("generated_by", "agent")
        kwargs.setdefault("target_format", "9:16")
        kwargs.setdefault("target_duration", 15)
        kwargs.setdefault("reference_ads", [])
        super().__init__(**kwargs)
