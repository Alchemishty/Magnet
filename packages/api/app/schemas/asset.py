from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

AssetType = Literal[
    "gameplay", "screenshot", "logo", "character", "audio"
]


class AssetCreate(BaseModel):
    project_id: UUID
    asset_type: AssetType
    s3_key: str
    filename: str
    content_type: str | None = None
    size_bytes: int | None = None
    duration_ms: int | None = None
    width: int | None = None
    height: int | None = None
    metadata_: dict | None = None


class AssetRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    asset_type: str
    s3_key: str
    filename: str
    content_type: str | None
    size_bytes: int | None
    duration_ms: int | None
    width: int | None
    height: int | None
    metadata_: dict
    created_at: datetime
    updated_at: datetime | None


class AssetUpdate(BaseModel):
    content_type: str | None = None
    size_bytes: int | None = None
    duration_ms: int | None = None
    width: int | None = None
    height: int | None = None
    metadata_: dict | None = None
