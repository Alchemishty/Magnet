"""Unit tests for BriefService."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.errors import NotFoundError
from app.models.brief import CreativeBrief
from app.schemas.brief import BriefUpdate
from app.services.brief_service import BriefService

REPO_PATH = "app.services.brief_service.BriefRepository"


@pytest.fixture
def session():
    return MagicMock()


@pytest.fixture
def mock_repo(session):
    with patch(REPO_PATH) as repo_cls:
        repo_instance = MagicMock()
        repo_cls.return_value = repo_instance
        service = BriefService(session)
        yield service, repo_instance


# ── list_briefs ──────────────────────────────────────────────


class TestListBriefs:
    def test_delegates_to_repo(self, mock_repo):
        service, repo = mock_repo
        project_id = uuid4()
        expected = [MagicMock(spec=CreativeBrief)]
        repo.list_by_project.return_value = expected

        result = service.list_briefs(project_id)

        repo.list_by_project.assert_called_once_with(
            project_id, None, 0, 100
        )
        assert result == expected

    def test_passes_optional_params(self, mock_repo):
        service, repo = mock_repo
        project_id = uuid4()
        repo.list_by_project.return_value = []

        service.list_briefs(project_id, status="draft", offset=10, limit=25)

        repo.list_by_project.assert_called_once_with(
            project_id, "draft", 10, 25
        )

    def test_returns_empty_list(self, mock_repo):
        service, repo = mock_repo
        repo.list_by_project.return_value = []

        result = service.list_briefs(uuid4())

        assert result == []


# ── get_brief ────────────────────────────────────────────────


class TestGetBrief:
    def test_returns_brief_when_found(self, mock_repo):
        service, repo = mock_repo
        brief_id = uuid4()
        expected = MagicMock(spec=CreativeBrief)
        repo.get_by_id.return_value = expected

        result = service.get_brief(brief_id)

        repo.get_by_id.assert_called_once_with(brief_id)
        assert result == expected

    def test_raises_not_found_when_missing(self, mock_repo):
        service, repo = mock_repo
        brief_id = uuid4()
        repo.get_by_id.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            service.get_brief(brief_id)

        assert exc_info.value.entity_name == "CreativeBrief"
        assert exc_info.value.entity_id == brief_id


# ── update_brief ─────────────────────────────────────────────


class TestUpdateBrief:
    def test_returns_updated_brief(self, mock_repo):
        service, repo = mock_repo
        brief_id = uuid4()
        data = BriefUpdate(script="new script")
        expected = MagicMock(spec=CreativeBrief)
        repo.update_from_schema.return_value = expected

        result = service.update_brief(brief_id, data)

        repo.update_from_schema.assert_called_once_with(brief_id, data)
        assert result == expected

    def test_raises_not_found_when_missing(self, mock_repo):
        service, repo = mock_repo
        brief_id = uuid4()
        data = BriefUpdate(status="approved")
        repo.update_from_schema.return_value = None

        with pytest.raises(NotFoundError) as exc_info:
            service.update_brief(brief_id, data)

        assert exc_info.value.entity_name == "CreativeBrief"
        assert exc_info.value.entity_id == brief_id


# ── delete_brief ─────────────────────────────────────────────


class TestDeleteBrief:
    def test_deletes_successfully(self, mock_repo):
        service, repo = mock_repo
        brief_id = uuid4()
        repo.delete.return_value = True

        result = service.delete_brief(brief_id)

        repo.delete.assert_called_once_with(brief_id)
        assert result is None

    def test_raises_not_found_when_missing(self, mock_repo):
        service, repo = mock_repo
        brief_id = uuid4()
        repo.delete.return_value = False

        with pytest.raises(NotFoundError) as exc_info:
            service.delete_brief(brief_id)

        assert exc_info.value.entity_name == "CreativeBrief"
        assert exc_info.value.entity_id == brief_id
