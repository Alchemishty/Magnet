from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.brief import CreativeBrief
from app.repositories.brief_repository import BriefRepository
from app.schemas.brief import BriefCreate, BriefUpdate


@pytest.fixture()
def mock_session():
    return MagicMock()


@pytest.fixture()
def repo(mock_session):
    return BriefRepository(mock_session)


class TestListByProject:
    def test_returns_briefs_for_project(self, repo, mock_session):
        briefs = [
            CreativeBrief(project_id=uuid4(), hook_type="fail_challenge"),
        ]
        query = MagicMock()
        mock_session.query.return_value = query
        query.filter.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = briefs

        result = repo.list_by_project(uuid4())

        assert result == briefs

    def test_filters_by_status(self, repo, mock_session):
        query = MagicMock()
        mock_session.query.return_value = query
        query.filter.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = []

        repo.list_by_project(uuid4(), status="approved")

        # filter called twice: project_id + status
        assert query.filter.call_count == 2

    def test_without_status_filter(self, repo, mock_session):
        query = MagicMock()
        mock_session.query.return_value = query
        query.filter.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = []

        repo.list_by_project(uuid4())

        assert query.filter.call_count == 1


class TestCreateFromSchema:
    def test_creates_brief(self, repo, mock_session):
        schema = BriefCreate(
            project_id=uuid4(),
            hook_type="fail_challenge",
        )

        result = repo.create_from_schema(schema)

        assert isinstance(result, CreativeBrief)
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()


class TestUpdateFromSchema:
    def test_updates_brief(self, repo, mock_session):
        brief = CreativeBrief(project_id=uuid4())
        entity_id = uuid4()
        mock_session.get.return_value = brief
        schema = BriefUpdate(status="approved")

        result = repo.update_from_schema(entity_id, schema)

        assert result is brief
        assert brief.status == "approved"
