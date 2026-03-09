from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate


@pytest.fixture()
def mock_session():
    return MagicMock()


@pytest.fixture()
def repo(mock_session):
    return UserRepository(mock_session)


class TestGetByEmail:
    def test_returns_user(self, repo, mock_session):
        user = User(email="a@b.com", name="Alice")
        query = MagicMock()
        mock_session.query.return_value = query
        query.filter.return_value = query
        query.first.return_value = user

        result = repo.get_by_email("a@b.com")

        assert result is user

    def test_returns_none_for_nonexistent(self, repo, mock_session):
        query = MagicMock()
        mock_session.query.return_value = query
        query.filter.return_value = query
        query.first.return_value = None

        result = repo.get_by_email("nope@b.com")

        assert result is None


class TestGetByClerkId:
    def test_returns_user(self, repo, mock_session):
        user = User(email="a@b.com", name="Alice", clerk_id="clerk_123")
        query = MagicMock()
        mock_session.query.return_value = query
        query.filter.return_value = query
        query.first.return_value = user

        result = repo.get_by_clerk_id("clerk_123")

        assert result is user

    def test_returns_none_for_nonexistent(self, repo, mock_session):
        query = MagicMock()
        mock_session.query.return_value = query
        query.filter.return_value = query
        query.first.return_value = None

        result = repo.get_by_clerk_id("clerk_nope")

        assert result is None


class TestCreateFromSchema:
    def test_creates_user(self, repo, mock_session):
        schema = UserCreate(email="a@b.com", name="Alice")

        result = repo.create_from_schema(schema)

        assert isinstance(result, User)
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()


class TestUpdateFromSchema:
    def test_updates_user(self, repo, mock_session):
        user = User(email="a@b.com", name="Alice")
        entity_id = uuid4()
        mock_session.get.return_value = user
        schema = UserUpdate(name="Bob")

        result = repo.update_from_schema(entity_id, schema)

        assert result is user
        assert user.name == "Bob"

    def test_excludes_unset_fields(self, repo, mock_session):
        user = User(email="a@b.com", name="Alice", role="creator")
        entity_id = uuid4()
        mock_session.get.return_value = user
        schema = UserUpdate(name="Bob")

        repo.update_from_schema(entity_id, schema)

        # role should remain unchanged since it wasn't set in the schema
        assert user.role == "creator"
