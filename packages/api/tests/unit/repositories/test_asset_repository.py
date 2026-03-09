from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.asset import Asset
from app.repositories.asset_repository import AssetRepository
from app.schemas.asset import AssetCreate, AssetUpdate


@pytest.fixture()
def mock_session():
    return MagicMock()


@pytest.fixture()
def repo(mock_session):
    return AssetRepository(mock_session)


class TestListByProject:
    def test_returns_assets_for_project(self, repo, mock_session):
        assets = [
            Asset(
                project_id=uuid4(),
                asset_type="gameplay",
                s3_key="a.mp4",
                filename="a.mp4",
            ),
        ]
        query = MagicMock()
        mock_session.query.return_value = query
        query.filter.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = assets

        result = repo.list_by_project(uuid4())

        assert result == assets

    def test_filters_by_asset_type(self, repo, mock_session):
        query = MagicMock()
        mock_session.query.return_value = query
        query.filter.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = []

        repo.list_by_project(uuid4(), asset_type="logo")

        # filter called twice: once for project_id, once for asset_type
        assert query.filter.call_count == 2

    def test_without_asset_type_filter(self, repo, mock_session):
        query = MagicMock()
        mock_session.query.return_value = query
        query.filter.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = []

        repo.list_by_project(uuid4())

        # filter called once: only for project_id
        assert query.filter.call_count == 1


class TestCreateFromSchema:
    def test_creates_asset(self, repo, mock_session):
        schema = AssetCreate(
            project_id=uuid4(),
            asset_type="gameplay",
            s3_key="uploads/test.mp4",
            filename="test.mp4",
        )

        result = repo.create_from_schema(schema)

        assert isinstance(result, Asset)
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()


class TestUpdateFromSchema:
    def test_updates_asset(self, repo, mock_session):
        asset = Asset(
            project_id=uuid4(),
            asset_type="gameplay",
            s3_key="a.mp4",
            filename="a.mp4",
        )
        entity_id = uuid4()
        mock_session.get.return_value = asset
        schema = AssetUpdate(size_bytes=1024)

        result = repo.update_from_schema(entity_id, schema)

        assert result is asset
        assert asset.size_bytes == 1024
