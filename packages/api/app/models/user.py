from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.project import Project


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    clerk_id: Mapped[str | None] = mapped_column(
        String(255), unique=True, nullable=True
    )
    role: Mapped[str] = mapped_column(String(50), server_default="creator")

    projects: Mapped[list[Project]] = relationship(
        back_populates="user",
    )

    def __init__(self, **kwargs):
        kwargs.setdefault("role", "creator")
        super().__init__(**kwargs)
