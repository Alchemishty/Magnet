from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.project import GameProfile
from app.repositories.game_profile_repository import GameProfileRepository
from app.schemas.project import GameProfileCreate, GameProfileUpdate


@pytest.fixture()
def mock_session():
    return MagicMock()


@pytest.fixture()
def repo(mock_session):
    return GameProfileRepository(mock_session)


class TestGetByProjectId:
    def test_returns_profile(self, repo, mock_session):
        profile = GameProfile(project_id=uuid4(), genre="puzzle")
        query = MagicMock()
        mock_session.query.return_value = query
        query.filter.return_value = query
        query.first.return_value = profile

        result = repo.get_by_project_id(uuid4())

        assert result is profile

    def test_returns_none_for_nonexistent(self, repo, mock_session):
        query = MagicMock()
        mock_session.query.return_value = query
        query.filter.return_value = query
        query.first.return_value = None

        result = repo.get_by_project_id(uuid4())

        assert result is None


class TestCreateFromSchema:
    def test_creates_profile(self, repo, mock_session):
        schema = GameProfileCreate(
            project_id=uuid4(),
            genre="puzzle",
            target_audience="casual",
        )

        result = repo.create_from_schema(schema)

        assert isinstance(result, GameProfile)
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()


class TestUpdateFromSchema:
    def test_updates_profile(self, repo, mock_session):
        profile = GameProfile(project_id=uuid4(), genre="puzzle")
        entity_id = uuid4()
        mock_session.get.return_value = profile
        schema = GameProfileUpdate(genre="action")

        result = repo.update_from_schema(entity_id, schema)

        assert result is profile
        assert profile.genre == "action"
