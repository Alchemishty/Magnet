"""Tests for project and game-profile routes."""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.errors import NotFoundError
from app.routes.dependencies import get_project_service
from app.routes.projects import router as projects_router

# ── helpers ───────────────────────────────────────────────────────


def _make_project(**overrides):
    defaults = {
        "id": uuid4(),
        "user_id": uuid4(),
        "name": "Test Project",
        "status": "active",
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
    }
    defaults.update(overrides)
    obj = MagicMock()
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


def _make_game_profile(**overrides):
    defaults = {
        "id": uuid4(),
        "project_id": uuid4(),
        "genre": "RPG",
        "target_audience": "teens",
        "core_mechanics": ["combat"],
        "art_style": "pixel",
        "brand_guidelines": {"tone": "fun"},
        "competitors": ["GameX"],
        "key_selling_points": ["unique combat"],
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
    }
    defaults.update(overrides)
    obj = MagicMock()
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


# ── fixtures ──────────────────────────────────────────────────────


@pytest.fixture()
def mock_service():
    return MagicMock()


@pytest.fixture()
def client(mock_service):
    test_app = FastAPI()
    test_app.include_router(projects_router)
    test_app.dependency_overrides[get_project_service] = lambda: mock_service
    return TestClient(test_app)


# ── POST /api/projects ───────────────────────────────────────────


class TestCreateProject:
    def test_returns_201(self, client, mock_service):
        project = _make_project()
        mock_service.create_project.return_value = project

        resp = client.post(
            "/api/projects",
            json={"name": "New", "user_id": str(project.user_id)},
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["id"] == str(project.id)
        assert data["name"] == "Test Project"


# ── GET /api/projects ────────────────────────────────────────────


class TestListProjects:
    def test_returns_list(self, client, mock_service):
        uid = uuid4()
        projects = [_make_project(user_id=uid), _make_project(user_id=uid)]
        mock_service.list_projects.return_value = projects

        resp = client.get(f"/api/projects?user_id={uid}")

        assert resp.status_code == 200
        assert len(resp.json()) == 2


# ── GET /api/projects/{id} ───────────────────────────────────────


class TestGetProject:
    def test_returns_200(self, client, mock_service):
        project = _make_project()
        mock_service.get_project.return_value = project

        resp = client.get(f"/api/projects/{project.id}")

        assert resp.status_code == 200
        assert resp.json()["id"] == str(project.id)

    def test_returns_404_when_not_found(self, client, mock_service):
        pid = uuid4()
        mock_service.get_project.side_effect = NotFoundError("Project", pid)

        resp = client.get(f"/api/projects/{pid}")

        assert resp.status_code == 404


# ── PATCH /api/projects/{id} ─────────────────────────────────────


class TestUpdateProject:
    def test_returns_200(self, client, mock_service):
        project = _make_project(name="Updated")
        mock_service.update_project.return_value = project

        resp = client.patch(
            f"/api/projects/{project.id}",
            json={"name": "Updated"},
        )

        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated"

    def test_returns_404_when_not_found(self, client, mock_service):
        pid = uuid4()
        mock_service.update_project.side_effect = NotFoundError("Project", pid)

        resp = client.patch(
            f"/api/projects/{pid}",
            json={"name": "Nope"},
        )

        assert resp.status_code == 404


# ── DELETE /api/projects/{id} ────────────────────────────────────


class TestDeleteProject:
    def test_returns_204(self, client, mock_service):
        pid = uuid4()
        mock_service.delete_project.return_value = None

        resp = client.delete(f"/api/projects/{pid}")

        assert resp.status_code == 204

    def test_returns_404_when_not_found(self, client, mock_service):
        pid = uuid4()
        mock_service.delete_project.side_effect = NotFoundError("Project", pid)

        resp = client.delete(f"/api/projects/{pid}")

        assert resp.status_code == 404


# ── POST /api/projects/{id}/game-profile ─────────────────────────


class TestCreateGameProfile:
    def test_returns_201_with_path_project_id(self, client, mock_service):
        pid = uuid4()
        profile = _make_game_profile(project_id=pid)
        mock_service.create_game_profile.return_value = profile

        resp = client.post(
            f"/api/projects/{pid}/game-profile",
            json={
                "project_id": str(uuid4()),  # body value should be overridden
                "genre": "RPG",
            },
        )

        assert resp.status_code == 201
        assert resp.json()["project_id"] == str(pid)
        # Verify the service was called with the path project_id
        call_data = mock_service.create_game_profile.call_args[0][0]
        assert call_data.project_id == pid


# ── GET /api/projects/{id}/game-profile ──────────────────────────


class TestGetGameProfile:
    def test_returns_200(self, client, mock_service):
        pid = uuid4()
        profile = _make_game_profile(project_id=pid)
        mock_service.get_game_profile.return_value = profile

        resp = client.get(f"/api/projects/{pid}/game-profile")

        assert resp.status_code == 200
        assert resp.json()["project_id"] == str(pid)

    def test_returns_404_when_not_found(self, client, mock_service):
        pid = uuid4()
        mock_service.get_game_profile.side_effect = NotFoundError(
            "GameProfile", pid
        )

        resp = client.get(f"/api/projects/{pid}/game-profile")

        assert resp.status_code == 404


# ── PATCH /api/projects/{id}/game-profile ────────────────────────


class TestUpdateGameProfile:
    def test_returns_200(self, client, mock_service):
        pid = uuid4()
        profile = _make_game_profile(project_id=pid, genre="Strategy")
        mock_service.update_game_profile.return_value = profile

        resp = client.patch(
            f"/api/projects/{pid}/game-profile",
            json={"genre": "Strategy"},
        )

        assert resp.status_code == 200
        assert resp.json()["genre"] == "Strategy"

    def test_returns_404_when_not_found(self, client, mock_service):
        pid = uuid4()
        mock_service.update_game_profile.side_effect = NotFoundError(
            "GameProfile", pid
        )

        resp = client.patch(
            f"/api/projects/{pid}/game-profile",
            json={"genre": "Strategy"},
        )

        assert resp.status_code == 404
