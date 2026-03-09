"""Tests for asset route endpoints."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.errors import NotFoundError
from app.routes.assets import router
from app.routes.dependencies import get_asset_service


def _make_asset(**overrides):
    defaults = {
        "id": uuid4(),
        "project_id": uuid4(),
        "asset_type": "gameplay",
        "s3_key": "assets/test.mp4",
        "filename": "test.mp4",
        "content_type": "video/mp4",
        "size_bytes": 1024,
        "duration_ms": 5000,
        "width": 1080,
        "height": 1920,
        "metadata_": {},
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
    }
    defaults.update(overrides)
    obj = MagicMock()
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


@pytest.fixture()
def mock_service():
    return MagicMock()


@pytest.fixture()
def client(mock_service):
    test_app = FastAPI()
    test_app.include_router(router)
    test_app.dependency_overrides[get_asset_service] = lambda: mock_service
    return TestClient(test_app)


# --- POST /api/projects/{project_id}/assets ---


class TestCreateAsset:
    def test_create_returns_201(self, client, mock_service):
        project_id = uuid4()
        asset = _make_asset(project_id=project_id)
        mock_service.create_asset.return_value = asset

        response = client.post(
            f"/api/projects/{project_id}/assets",
            json={
                "project_id": str(uuid4()),  # should be overridden
                "asset_type": "gameplay",
                "s3_key": "assets/test.mp4",
                "filename": "test.mp4",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == str(asset.id)
        assert data["project_id"] == str(project_id)

        # Verify project_id from URL was used
        call_args = mock_service.create_asset.call_args[0][0]
        assert call_args.project_id == project_id

    def test_create_project_not_found_returns_404(self, client, mock_service):
        project_id = uuid4()
        mock_service.create_asset.side_effect = NotFoundError(
            "Project", project_id
        )

        response = client.post(
            f"/api/projects/{project_id}/assets",
            json={
                "project_id": str(project_id),
                "asset_type": "gameplay",
                "s3_key": "assets/test.mp4",
                "filename": "test.mp4",
            },
        )

        assert response.status_code == 404


# --- GET /api/projects/{project_id}/assets ---


class TestListAssets:
    def test_list_returns_200(self, client, mock_service):
        project_id = uuid4()
        assets = [_make_asset(project_id=project_id) for _ in range(3)]
        mock_service.list_assets.return_value = assets

        response = client.get(f"/api/projects/{project_id}/assets")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_list_with_query_params(self, client, mock_service):
        project_id = uuid4()
        mock_service.list_assets.return_value = []

        response = client.get(
            f"/api/projects/{project_id}/assets",
            params={"asset_type": "logo", "offset": 10, "limit": 5},
        )

        assert response.status_code == 200
        mock_service.list_assets.assert_called_once_with(
            project_id, asset_type="logo", offset=10, limit=5
        )


# --- GET /api/assets/{asset_id} ---


class TestGetAsset:
    def test_get_returns_200(self, client, mock_service):
        asset = _make_asset()
        mock_service.get_asset.return_value = asset

        response = client.get(f"/api/assets/{asset.id}")

        assert response.status_code == 200
        assert response.json()["id"] == str(asset.id)

    def test_get_not_found_returns_404(self, client, mock_service):
        asset_id = uuid4()
        mock_service.get_asset.side_effect = NotFoundError("Asset", asset_id)

        response = client.get(f"/api/assets/{asset_id}")

        assert response.status_code == 404


# --- DELETE /api/assets/{asset_id} ---


class TestDeleteAsset:
    def test_delete_returns_204(self, client, mock_service):
        asset_id = uuid4()
        mock_service.delete_asset.return_value = None

        response = client.delete(f"/api/assets/{asset_id}")

        assert response.status_code == 204
        assert response.content == b""

    def test_delete_not_found_returns_404(self, client, mock_service):
        asset_id = uuid4()
        mock_service.delete_asset.side_effect = NotFoundError(
            "Asset", asset_id
        )

        response = client.delete(f"/api/assets/{asset_id}")

        assert response.status_code == 404
