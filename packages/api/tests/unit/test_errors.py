"""Tests for domain error classes."""

from app.errors import (
    DatabaseError,
    ExternalProviderError,
    NotFoundError,
    ValidationError,
)


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


class TestExternalProviderError:
    def test_attributes(self):
        err = ExternalProviderError("claude", "rate limit exceeded")
        assert err.provider_name == "claude"
        assert err.message == "rate limit exceeded"

    def test_message_includes_provider_and_detail(self):
        err = ExternalProviderError("openai", "timeout")
        assert "openai" in str(err)
        assert "timeout" in str(err)

    def test_is_exception(self):
        err = ExternalProviderError("claude", "error")
        assert isinstance(err, Exception)
