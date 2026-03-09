from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


@pytest.fixture()
def mock_session():
    return MagicMock()


@pytest.fixture()
def repo(mock_session):
    return ProjectRepository(mock_session)


class TestListByUser:
    def test_returns_projects_for_user(self, repo, mock_session):
        projects = [
            Project(user_id=uuid4(), name="Game A"),
            Project(user_id=uuid4(), name="Game B"),
        ]
        query = MagicMock()
        mock_session.query.return_value = query
        query.filter.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = projects

        result = repo.list_by_user(uuid4())

        assert result == projects

    def test_respects_offset_limit(self, repo, mock_session):
        query = MagicMock()
        mock_session.query.return_value = query
        query.filter.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = []

        repo.list_by_user(uuid4(), offset=5, limit=10)

        query.offset.assert_called_once_with(5)
        query.limit.assert_called_once_with(10)


class TestCreateFromSchema:
    def test_creates_project(self, repo, mock_session):
        schema = ProjectCreate(name="Test Game", user_id=uuid4())

        result = repo.create_from_schema(schema)

        assert isinstance(result, Project)
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()


class TestUpdateFromSchema:
    def test_updates_project(self, repo, mock_session):
        project = Project(user_id=uuid4(), name="Old Name")
        entity_id = uuid4()
        mock_session.get.return_value = project
        schema = ProjectUpdate(name="New Name")

        result = repo.update_from_schema(entity_id, schema)

        assert result is project
        assert project.name == "New Name"
