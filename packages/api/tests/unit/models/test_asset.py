"""Tests for the Asset model."""

from uuid import uuid4

from sqlalchemy import inspect

from app.models.asset import Asset


class TestAsset:
    def test_table_name(self):
        assert Asset.__tablename__ == "assets"

    def test_has_required_columns(self):
        mapper = inspect(Asset)
        columns = {c.key for c in mapper.columns}

        assert "id" in columns
        assert "project_id" in columns
        assert "asset_type" in columns
        assert "s3_key" in columns
        assert "filename" in columns
        assert "content_type" in columns
        assert "size_bytes" in columns
        assert "duration_ms" in columns
        assert "width" in columns
        assert "height" in columns
        assert "metadata" in columns

    def test_asset_type_is_not_nullable(self):
        mapper = inspect(Asset)
        col = mapper.columns["asset_type"]

        assert col.nullable is False

    def test_duration_is_nullable(self):
        mapper = inspect(Asset)
        col = mapper.columns["duration_ms"]

        assert col.nullable is True

    def test_metadata_defaults_to_empty_dict(self):
        asset = Asset(
            project_id=uuid4(),
            asset_type="gameplay",
            s3_key="uploads/test.mp4",
            filename="test.mp4",
        )

        assert asset.metadata_ == {}

    def test_has_project_relationship(self):
        assert hasattr(Asset, "project")
