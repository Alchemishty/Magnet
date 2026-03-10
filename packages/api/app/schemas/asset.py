from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

AssetType = Literal["gameplay", "screenshot", "logo", "character", "audio"]


class AssetCreateBody(BaseModel):
    asset_type: AssetType
    s3_key: str
    filename: str
    content_type: str | None = None
    size_bytes: int | None = None
    duration_ms: int | None = None
    width: int | None = None
    height: int | None = None
    metadata_: dict | None = None


class AssetCreate(AssetCreateBody):
    project_id: UUID


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


class PresignedUploadRequest(BaseModel):
    filename: str
    content_type: str
    asset_type: AssetType


class PresignedUploadResponse(BaseModel):
    upload_url: str
    s3_key: str
