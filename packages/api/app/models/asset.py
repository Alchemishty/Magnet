from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import BigInteger, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.project import Project


class Asset(BaseModel):
    __tablename__ = "assets"

    project_id: Mapped[UUID] = mapped_column(
        ForeignKey("projects.id"), nullable=False, index=True
    )
    asset_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False)
    filename: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    content_type: Mapped[str | None] = mapped_column(String(100))
    size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    width: Mapped[int | None] = mapped_column(Integer)
    height: Mapped[int | None] = mapped_column(Integer)
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, server_default="{}"
    )

    project: Mapped[Project] = relationship(back_populates="assets")

    def __init__(self, **kwargs):
        kwargs.setdefault("metadata_", {})
        super().__init__(**kwargs)
