from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.asset import Asset
    from app.models.brief import CreativeBrief
    from app.models.user import User


class Project(BaseModel):
    __tablename__ = "projects"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), server_default="active")

    user: Mapped[User] = relationship(back_populates="projects")
    game_profile: Mapped[GameProfile | None] = relationship(
        back_populates="project", uselist=False
    )
    assets: Mapped[list[Asset]] = relationship(back_populates="project")
    briefs: Mapped[list[CreativeBrief]] = relationship(back_populates="project")

    def __init__(self, **kwargs):
        kwargs.setdefault("status", "active")
        super().__init__(**kwargs)


class GameProfile(BaseModel):
    __tablename__ = "game_profiles"

    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id"), unique=True, nullable=False
    )
    genre: Mapped[str | None] = mapped_column(String(100))
    target_audience: Mapped[str | None] = mapped_column(String(255))
    core_mechanics: Mapped[list | None] = mapped_column(JSONB)
    art_style: Mapped[str | None] = mapped_column(String(100))
    brand_guidelines: Mapped[dict | None] = mapped_column(JSONB)
    competitors: Mapped[list | None] = mapped_column(JSONB)
    key_selling_points: Mapped[list | None] = mapped_column(JSONB)

    project: Mapped[Project] = relationship(back_populates="game_profile")
