from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.errors import DatabaseError
from app.models.user import User
from app.repositories.base import BaseRepository


@pytest.fixture()
def mock_session():
    return MagicMock()


@pytest.fixture()
def repo(mock_session):
    return BaseRepository(mock_session, User)


class TestCreate:
    def test_create_adds_and_flushes(self, repo, mock_session):
        data = {"email": "a@b.com", "name": "Alice"}
        result = repo.create(data)

        assert isinstance(result, User)
        mock_session.add.assert_called_once_with(result)
        mock_session.flush.assert_called_once()

    def test_create_wraps_sqlalchemy_error(self, repo, mock_session):
        mock_session.flush.side_effect = SQLAlchemyError("boom")

        with pytest.raises(DatabaseError):
            repo.create({"email": "a@b.com", "name": "Alice"})


class TestGetById:
    def test_get_by_id_returns_entity(self, repo, mock_session):
        user = User(email="a@b.com", name="Alice")
        entity_id = uuid4()
        mock_session.get.return_value = user

        result = repo.get_by_id(entity_id)

        assert result is user
        mock_session.get.assert_called_once_with(User, entity_id)

    def test_get_by_id_returns_none(self, repo, mock_session):
        mock_session.get.return_value = None

        result = repo.get_by_id(uuid4())

        assert result is None


class TestList:
    def test_list_returns_all(self, repo, mock_session):
        users = [
            User(email="a@b.com", name="A"),
            User(email="b@b.com", name="B"),
        ]
        query = MagicMock()
        mock_session.query.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = users

        result = repo.list()

        assert result == users
        mock_session.query.assert_called_once_with(User)

    def test_list_with_filters(self, repo, mock_session):
        query = MagicMock()
        mock_session.query.return_value = query
        query.filter.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = []

        repo.list(filters={"role": "admin"})

        query.filter.assert_called_once()

    def test_list_with_offset_limit(self, repo, mock_session):
        query = MagicMock()
        mock_session.query.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = []

        repo.list(offset=10, limit=5)

        query.offset.assert_called_once_with(10)
        query.limit.assert_called_once_with(5)


class TestUpdate:
    def test_update_applies_changes(self, repo, mock_session):
        user = User(email="a@b.com", name="Alice")
        entity_id = uuid4()
        mock_session.get.return_value = user

        result = repo.update(entity_id, {"name": "Bob"})

        assert result is user
        assert user.name == "Bob"
        mock_session.flush.assert_called_once()

    def test_update_returns_none_when_not_found(self, repo, mock_session):
        mock_session.get.return_value = None

        result = repo.update(uuid4(), {"name": "Bob"})

        assert result is None
        mock_session.flush.assert_not_called()


class TestDelete:
    def test_delete_returns_true(self, repo, mock_session):
        user = User(email="a@b.com", name="Alice")
        mock_session.get.return_value = user

        result = repo.delete(uuid4())

        assert result is True
        mock_session.delete.assert_called_once_with(user)
        mock_session.flush.assert_called_once()

    def test_delete_returns_false_when_not_found(self, repo, mock_session):
        mock_session.get.return_value = None

        result = repo.delete(uuid4())

        assert result is False
        mock_session.delete.assert_not_called()
