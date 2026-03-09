"""Unit tests for AssetService."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.errors import NotFoundError
from app.models.asset import Asset
from app.schemas.asset import AssetCreate
from app.services.asset_service import AssetService

MODULE = "app.services.asset_service"


@pytest.fixture
def session():
    return MagicMock()


@pytest.fixture
def asset_repo():
    with patch(f"{MODULE}.AssetRepository") as mock_cls:
        yield mock_cls.return_value


@pytest.fixture
def project_repo():
    with patch(f"{MODULE}.ProjectRepository") as mock_cls:
        yield mock_cls.return_value


@pytest.fixture
def service(session, asset_repo, project_repo):
    return AssetService(session)


# ---- create_asset ----


class TestCreateAsset:
    def test_creates_asset_when_project_exists(
        self, service, asset_repo, project_repo
    ):
        project_id = uuid4()
        data = AssetCreate(
            project_id=project_id,
            asset_type="logo",
            s3_key="assets/logo.png",
            filename="logo.png",
        )
        project_repo.get_by_id.return_value = MagicMock()
        expected = MagicMock(spec=Asset)
        asset_repo.create_from_schema.return_value = expected

        result = service.create_asset(data)

        project_repo.get_by_id.assert_called_once_with(project_id)
        asset_repo.create_from_schema.assert_called_once_with(data)
        assert result is expected

    def test_raises_not_found_when_project_missing(
        self, service, project_repo
    ):
        project_id = uuid4()
        data = AssetCreate(
            project_id=project_id,
            asset_type="logo",
            s3_key="assets/logo.png",
            filename="logo.png",
        )
        project_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            service.create_asset(data)

        assert exc_info.value.entity_name == "Project"
        assert exc_info.value.entity_id == project_id


# ---- list_assets ----


class TestListAssets:
    def test_returns_assets(self, service, asset_repo):
        project_id = uuid4()
        expected = [MagicMock(spec=Asset)]
        asset_repo.list_by_project.return_value = expected

        result = service.list_assets(project_id)

        asset_repo.list_by_project.assert_called_once_with(
            project_id, None, 0, 100
        )
        assert result is expected

    def test_passes_filters(self, service, asset_repo):
        project_id = uuid4()
        asset_repo.list_by_project.return_value = []

        service.list_assets(
            project_id, asset_type="logo", offset=10, limit=50
        )

        asset_repo.list_by_project.assert_called_once_with(
            project_id, "logo", 10, 50
        )


# ---- get_asset ----


class TestGetAsset:
    def test_returns_asset(self, service, asset_repo):
        asset_id = uuid4()
        expected = MagicMock(spec=Asset)
        asset_repo.get_by_id.return_value = expected

        result = service.get_asset(asset_id)

        asset_repo.get_by_id.assert_called_once_with(asset_id)
        assert result is expected

    def test_raises_not_found(self, service, asset_repo):
        asset_id = uuid4()
        asset_repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            service.get_asset(asset_id)

        assert exc_info.value.entity_name == "Asset"
        assert exc_info.value.entity_id == asset_id


# ---- delete_asset ----


class TestDeleteAsset:
    def test_deletes_asset(self, service, asset_repo):
        asset_id = uuid4()
        asset_repo.delete.return_value = True

        service.delete_asset(asset_id)

        asset_repo.delete.assert_called_once_with(asset_id)

    def test_raises_not_found(self, service, asset_repo):
        asset_id = uuid4()
        asset_repo.delete.return_value = False

        with pytest.raises(NotFoundError) as exc_info:
            service.delete_asset(asset_id)

        assert exc_info.value.entity_name == "Asset"
        assert exc_info.value.entity_id == asset_id
