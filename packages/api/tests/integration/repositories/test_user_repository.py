import pytest

from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate


@pytest.mark.integration
class TestUserRepositoryIntegration:
    def test_create_and_get_by_id(self, db_session):
        repo = UserRepository(db_session)
        schema = UserCreate(email="alice@example.com", name="Alice")

        user = repo.create_from_schema(schema)

        assert user.id is not None
        assert user.email == "alice@example.com"

        fetched = repo.get_by_id(user.id)
        assert fetched is not None
        assert fetched.email == "alice@example.com"

    def test_get_by_email(self, db_session):
        repo = UserRepository(db_session)
        schema = UserCreate(email="bob@example.com", name="Bob")
        repo.create_from_schema(schema)

        result = repo.get_by_email("bob@example.com")

        assert result is not None
        assert result.name == "Bob"

    def test_get_by_email_returns_none(self, db_session):
        repo = UserRepository(db_session)

        result = repo.get_by_email("nobody@example.com")

        assert result is None

    def test_get_by_clerk_id(self, db_session):
        repo = UserRepository(db_session)
        schema = UserCreate(
            email="clerk@example.com",
            name="Clerk User",
            clerk_id="clerk_abc",
        )
        repo.create_from_schema(schema)

        result = repo.get_by_clerk_id("clerk_abc")

        assert result is not None
        assert result.email == "clerk@example.com"

    def test_update_from_schema(self, db_session):
        repo = UserRepository(db_session)
        schema = UserCreate(email="update@example.com", name="Before")
        user = repo.create_from_schema(schema)

        update_schema = UserUpdate(name="After")
        updated = repo.update_from_schema(user.id, update_schema)

        assert updated is not None
        assert updated.name == "After"

    def test_list_users(self, db_session):
        repo = UserRepository(db_session)
        repo.create_from_schema(
            UserCreate(email="list1@example.com", name="One")
        )
        repo.create_from_schema(
            UserCreate(email="list2@example.com", name="Two")
        )

        users = repo.list()

        assert len(users) >= 2

    def test_delete_user(self, db_session):
        repo = UserRepository(db_session)
        schema = UserCreate(email="delete@example.com", name="Delete Me")
        user = repo.create_from_schema(schema)

        result = repo.delete(user.id)

        assert result is True
        assert repo.get_by_id(user.id) is None
