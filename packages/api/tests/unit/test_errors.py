"""Tests for domain error classes."""

from app.errors import DatabaseError, NotFoundError, ValidationError


class TestNotFoundError:
    def test_message_includes_entity_and_id(self):
        err = NotFoundError("Project", "abc-123")
        assert "Project" in str(err)
        assert "abc-123" in str(err)

    def test_attributes(self):
        err = NotFoundError("Brief", 42)
        assert err.entity_name == "Brief"
        assert err.entity_id == 42


class TestDatabaseError:
    def test_default_message(self):
        err = DatabaseError()
        assert "database error" in str(err).lower()

    def test_custom_message(self):
        err = DatabaseError("connection lost")
        assert "connection lost" in str(err)


class TestValidationError:
    def test_message(self):
        err = ValidationError("GameProfile required")
        assert "GameProfile required" in str(err)

    def test_is_exception(self):
        err = ValidationError("bad input")
        assert isinstance(err, Exception)
