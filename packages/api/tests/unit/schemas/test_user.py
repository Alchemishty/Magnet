"""Tests for User schemas."""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate, UserRead, UserUpdate


class TestUserCreate:
    def test_valid_creation(self):
        schema = UserCreate(email="test@example.com", name="Test")

        assert schema.email == "test@example.com"
        assert schema.name == "Test"
        assert schema.role == "creator"

    def test_role_defaults_to_creator(self):
        schema = UserCreate(email="a@b.com", name="A")

        assert schema.role == "creator"

    def test_rejects_missing_email(self):
        with pytest.raises(ValidationError):
            UserCreate(name="Test")

    def test_rejects_missing_name(self):
        with pytest.raises(ValidationError):
            UserCreate(email="test@example.com")


class TestUserRead:
    def test_from_attributes(self):
        now = datetime.now(timezone.utc)
        obj = SimpleNamespace(
            id=uuid4(),
            email="test@example.com",
            name="Test",
            clerk_id=None,
            role="creator",
            created_at=now,
            updated_at=None,
        )

        schema = UserRead.model_validate(obj, from_attributes=True)

        assert schema.email == "test@example.com"
        assert schema.created_at == now


class TestUserUpdate:
    def test_all_fields_optional(self):
        schema = UserUpdate()

        assert schema.name is None
        assert schema.role is None

    def test_partial_update(self):
        schema = UserUpdate(name="New Name")

        assert schema.name == "New Name"
        assert schema.role is None
