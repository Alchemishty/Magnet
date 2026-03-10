"""Unit tests for brief routes."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.agents.concept_agent import ConceptAgentError
from app.errors import (
    DatabaseError,
    ExternalProviderError,
    NotFoundError,
    ValidationError,
)
from app.routes.briefs import router
from app.routes.dependencies import (
    get_brief_service,
    get_concept_agent,
    get_concept_service,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_brief(**overrides):
    """Create a mock object that looks like a CreativeBrief ORM instance."""
    defaults = {
        "id": uuid4(),
        "project_id": uuid4(),
        "hook_type": "Fail/Challenge",
        "narrative_angle": "test angle",
        "script": "test script",
        "voiceover_text": None,
        "target_emotion": "excitement",
        "cta_text": None,
        "reference_ads": [],
        "target_format": "9:16",
        "target_duration": 15,
        "status": "draft",
        "generated_by": "agent",
        "scene_plan": None,
        "created_at": datetime.now(timezone.utc),
        "updated_at": None,
    }
    defaults.update(overrides)
    obj = MagicMock()
    for k, v in defaults.items():
        setattr(obj, k, v)
    return obj


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def mock_brief_service():
    return MagicMock()


@pytest.fixture()
def mock_concept_service():
    return AsyncMock()


@pytest.fixture()
def mock_concept_agent():
    return MagicMock()


@pytest.fixture()
def client(mock_brief_service, mock_concept_service, mock_concept_agent):
    test_app = FastAPI()
    test_app.include_router(router)
    test_app.dependency_overrides[get_brief_service] = lambda: mock_brief_service
    test_app.dependency_overrides[get_concept_service] = lambda: mock_concept_service
    test_app.dependency_overrides[get_concept_agent] = lambda: mock_concept_agent
    return TestClient(test_app)


# ---------------------------------------------------------------------------
# GET /api/projects/{project_id}/briefs
# ---------------------------------------------------------------------------


class TestListBriefs:
    def test_returns_list_of_briefs(self, client, mock_brief_service):
        project_id = uuid4()
        briefs = [_make_brief(project_id=project_id) for _ in range(3)]
        mock_brief_service.list_briefs.return_value = briefs

        resp = client.get(f"/api/projects/{project_id}/briefs")

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        mock_brief_service.list_briefs.assert_called_once_with(project_id, None, 0, 100)

    def test_passes_query_params(self, client, mock_brief_service):
        project_id = uuid4()
        mock_brief_service.list_briefs.return_value = []

        resp = client.get(
            f"/api/projects/{project_id}/briefs",
            params={"status": "approved", "offset": 10, "limit": 5},
        )

        assert resp.status_code == 200
        mock_brief_service.list_briefs.assert_called_once_with(
            project_id, "approved", 10, 5
        )

    def test_returns_empty_list(self, client, mock_brief_service):
        mock_brief_service.list_briefs.return_value = []
        resp = client.get(f"/api/projects/{uuid4()}/briefs")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_database_error_returns_500(self, client, mock_brief_service):
        mock_brief_service.list_briefs.side_effect = DatabaseError("db down")
        resp = client.get(f"/api/projects/{uuid4()}/briefs")
        assert resp.status_code == 500
        assert resp.json()["detail"] == "db down"


# ---------------------------------------------------------------------------
# POST /api/projects/{project_id}/concepts
# ---------------------------------------------------------------------------


class TestGenerateConcepts:
    def test_returns_briefs(self, client, mock_concept_service):
        project_id = uuid4()
        briefs = [_make_brief(project_id=project_id) for _ in range(3)]
        mock_concept_service.generate_concepts.return_value = briefs

        resp = client.post(f"/api/projects/{project_id}/concepts")

        assert resp.status_code == 201
        assert len(resp.json()) == 3
        mock_concept_service.generate_concepts.assert_called_once()

    def test_not_found_returns_404(self, client, mock_concept_service):
        project_id = uuid4()
        mock_concept_service.generate_concepts.side_effect = NotFoundError(
            "GameProfile", project_id
        )

        resp = client.post(f"/api/projects/{project_id}/concepts")

        assert resp.status_code == 404

    def test_validation_error_returns_422(self, client, mock_concept_service):
        mock_concept_service.generate_concepts.side_effect = ValidationError(
            "GameProfile requires genre"
        )

        resp = client.post(f"/api/projects/{uuid4()}/concepts")

        assert resp.status_code == 422

    def test_external_provider_error_returns_502(self, client, mock_concept_service):
        mock_concept_service.generate_concepts.side_effect = ExternalProviderError(
            "claude", "rate limited"
        )

        resp = client.post(f"/api/projects/{uuid4()}/concepts")

        assert resp.status_code == 502
        assert "claude" in resp.json()["detail"]

    def test_concept_agent_error_returns_502(self, client, mock_concept_service):
        mock_concept_service.generate_concepts.side_effect = ConceptAgentError(
            "malformed response"
        )

        resp = client.post(f"/api/projects/{uuid4()}/concepts")

        assert resp.status_code == 502

    def test_value_error_returns_500_config_error(
        self, client, mock_concept_service
    ):
        mock_concept_service.generate_concepts.side_effect = ValueError(
            "ANTHROPIC_API_KEY environment variable is required"
        )

        resp = client.post(f"/api/projects/{uuid4()}/concepts")

        assert resp.status_code == 500
        assert "LLM configuration error" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# GET /api/briefs/{brief_id}
# ---------------------------------------------------------------------------


class TestGetBrief:
    def test_returns_brief(self, client, mock_brief_service):
        brief = _make_brief()
        mock_brief_service.get_brief.return_value = brief

        resp = client.get(f"/api/briefs/{brief.id}")

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == str(brief.id)
        assert data["hook_type"] == "Fail/Challenge"

    def test_not_found_returns_404(self, client, mock_brief_service):
        brief_id = uuid4()
        mock_brief_service.get_brief.side_effect = NotFoundError(
            "CreativeBrief", brief_id
        )

        resp = client.get(f"/api/briefs/{brief_id}")

        assert resp.status_code == 404
        assert str(brief_id) in resp.json()["detail"]

    def test_database_error_returns_500(self, client, mock_brief_service):
        mock_brief_service.get_brief.side_effect = DatabaseError("conn lost")
        resp = client.get(f"/api/briefs/{uuid4()}")
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# PATCH /api/briefs/{brief_id}
# ---------------------------------------------------------------------------


class TestUpdateBrief:
    def test_updates_and_returns_brief(self, client, mock_brief_service):
        brief = _make_brief(status="approved")
        mock_brief_service.update_brief.return_value = brief

        resp = client.patch(
            f"/api/briefs/{brief.id}",
            json={"status": "approved"},
        )

        assert resp.status_code == 200
        assert resp.json()["status"] == "approved"
        mock_brief_service.update_brief.assert_called_once()

    def test_not_found_returns_404(self, client, mock_brief_service):
        brief_id = uuid4()
        mock_brief_service.update_brief.side_effect = NotFoundError(
            "CreativeBrief", brief_id
        )

        resp = client.patch(
            f"/api/briefs/{brief_id}",
            json={"status": "approved"},
        )

        assert resp.status_code == 404

    def test_database_error_returns_500(self, client, mock_brief_service):
        mock_brief_service.update_brief.side_effect = DatabaseError("fail")
        resp = client.patch(
            f"/api/briefs/{uuid4()}",
            json={"status": "draft"},
        )
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# DELETE /api/briefs/{brief_id}
# ---------------------------------------------------------------------------


class TestDeleteBrief:
    def test_deletes_and_returns_204(self, client, mock_brief_service):
        brief_id = uuid4()
        mock_brief_service.delete_brief.return_value = None

        resp = client.delete(f"/api/briefs/{brief_id}")

        assert resp.status_code == 204
        assert resp.content == b""
        mock_brief_service.delete_brief.assert_called_once_with(brief_id)

    def test_not_found_returns_404(self, client, mock_brief_service):
        brief_id = uuid4()
        mock_brief_service.delete_brief.side_effect = NotFoundError(
            "CreativeBrief", brief_id
        )

        resp = client.delete(f"/api/briefs/{brief_id}")

        assert resp.status_code == 404

    def test_database_error_returns_500(self, client, mock_brief_service):
        mock_brief_service.delete_brief.side_effect = DatabaseError("boom")
        resp = client.delete(f"/api/briefs/{uuid4()}")
        assert resp.status_code == 500
