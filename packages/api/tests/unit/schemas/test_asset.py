"""Tests for Asset schemas."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.asset import (
    AssetCreate,
    PresignedUploadRequest,
    PresignedUploadResponse,
)


class TestAssetCreate:
    def test_valid_creation(self):
        schema = AssetCreate(
            project_id=uuid4(),
            asset_type="gameplay",
            s3_key="uploads/test.mp4",
            filename="test.mp4",
        )

        assert schema.asset_type == "gameplay"

    def test_rejects_invalid_asset_type(self):
        with pytest.raises(ValidationError):
            AssetCreate(
                project_id=uuid4(),
                asset_type="invalid",
                s3_key="x",
                filename="x",
            )

    def test_accepts_all_valid_asset_types(self):
        for asset_type in [
            "gameplay",
            "screenshot",
            "logo",
            "character",
            "audio",
        ]:
            schema = AssetCreate(
                project_id=uuid4(),
                asset_type=asset_type,
                s3_key="x",
                filename="x",
            )

            assert schema.asset_type == asset_type

    def test_rejects_missing_required_fields(self):
        with pytest.raises(ValidationError):
            AssetCreate(project_id=uuid4())


class TestPresignedUploadRequest:
    def test_valid_request(self):
        req = PresignedUploadRequest(
            filename="video.mp4",
            content_type="video/mp4",
            asset_type="gameplay",
        )
        assert req.filename == "video.mp4"

    def test_rejects_invalid_asset_type(self):
        with pytest.raises(ValidationError):
            PresignedUploadRequest(
                filename="x", content_type="x", asset_type="invalid"
            )


class TestPresignedUploadResponse:
    def test_valid_response(self):
        resp = PresignedUploadResponse(
            upload_url="https://s3/presigned",
            s3_key="uploads/abc/video.mp4",
        )
        assert resp.upload_url == "https://s3/presigned"
        assert resp.s3_key == "uploads/abc/video.mp4"
