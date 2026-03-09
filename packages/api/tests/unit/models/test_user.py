"""Tests for the User model."""

from sqlalchemy import inspect

from app.models.user import User


class TestUser:
    def test_table_name(self):
        assert User.__tablename__ == "users"

    def test_has_required_columns(self):
        mapper = inspect(User)
        columns = {c.key for c in mapper.columns}

        assert "id" in columns
        assert "email" in columns
        assert "name" in columns
        assert "clerk_id" in columns
        assert "role" in columns
        assert "created_at" in columns
        assert "updated_at" in columns

    def test_email_is_unique(self):
        mapper = inspect(User)
        email_col = mapper.columns["email"]

        assert email_col.unique is True

    def test_email_is_not_nullable(self):
        mapper = inspect(User)
        email_col = mapper.columns["email"]

        assert email_col.nullable is False

    def test_role_defaults_to_creator(self):
        user = User(email="test@example.com", name="Test")

        assert user.role == "creator"

    def test_clerk_id_is_nullable(self):
        mapper = inspect(User)
        clerk_col = mapper.columns["clerk_id"]

        assert clerk_col.nullable is True

    def test_has_projects_relationship(self):
        assert hasattr(User, "projects")
