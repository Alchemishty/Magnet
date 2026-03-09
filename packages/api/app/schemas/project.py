from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ProjectCreate(BaseModel):
    name: str
    user_id: UUID


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    status: str
    created_at: datetime
    updated_at: datetime | None


class ProjectUpdate(BaseModel):
    name: str | None = None
    status: str | None = None


class GameProfileCreate(BaseModel):
    project_id: UUID
    genre: str | None = None
    target_audience: str | None = None
    core_mechanics: list[str] | None = None
    art_style: str | None = None
    brand_guidelines: dict | None = None
    competitors: list[str] | None = None
    key_selling_points: list[str] | None = None


class GameProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    genre: str | None
    target_audience: str | None
    core_mechanics: list | None
    art_style: str | None
    brand_guidelines: dict | None
    competitors: list | None
    key_selling_points: list | None
    created_at: datetime
    updated_at: datetime | None


class GameProfileUpdate(BaseModel):
    genre: str | None = None
    target_audience: str | None = None
    core_mechanics: list[str] | None = None
    art_style: str | None = None
    brand_guidelines: dict | None = None
    competitors: list[str] | None = None
    key_selling_points: list[str] | None = None
