"""Tests for ClaudeProvider."""

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.errors import ExternalProviderError
from app.providers.llm.claude import ClaudeProvider


@pytest.fixture
def provider():
    return ClaudeProvider(api_key="test-key")


def _make_text_response(content: dict) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "content": [{"type": "text", "text": json.dumps(content)}],
            "stop_reason": "end_turn",
        },
    )


def _make_tool_response(content: dict) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "content": [
                {
                    "type": "tool_use",
                    "id": "call_1",
                    "name": "structured_output",
                    "input": content,
                }
            ],
            "stop_reason": "tool_use",
        },
    )


class TestClaudeProviderInit:
    def test_default_model(self, provider):
        assert provider._model == "claude-sonnet-4-20250514"

    def test_custom_model(self):
        p = ClaudeProvider(api_key="k", model="claude-haiku-4-5-20251001")
        assert p._model == "claude-haiku-4-5-20251001"

    def test_sets_headers(self, provider):
        headers = provider._client.headers
        assert headers["x-api-key"] == "test-key"
        assert headers["anthropic-version"] == "2023-06-01"


class TestClaudeProviderLifecycle:
    async def test_aclose_closes_client(self, provider):
        with patch.object(
            provider._client, "aclose", new_callable=AsyncMock
        ) as mock_close:
            await provider.aclose()
            mock_close.assert_called_once()


class TestClaudeProviderGenerate:
    async def test_without_schema_parses_text_response(self, provider):
        expected = {"directions": [{"hook_type": "Fail"}]}
        mock_response = _make_text_response(expected)

        with patch.object(
            provider._client, "post", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await provider.generate([{"role": "user", "content": "hello"}])

        assert result == expected

    async def test_with_schema_uses_tool_use(self, provider):
        expected = {"directions": [{"hook_type": "Fail"}]}
        mock_response = _make_tool_response(expected)
        schema = {"type": "object", "properties": {"directions": {"type": "array"}}}

        with patch.object(
            provider._client, "post", new_callable=AsyncMock, return_value=mock_response
        ) as mock_post:
            result = await provider.generate(
                [{"role": "user", "content": "hello"}],
                schema=schema,
            )

        assert result == expected
        call_body = mock_post.call_args[1]["json"]
        assert "tools" in call_body
        assert call_body["tools"][0]["name"] == "structured_output"

    async def test_extracts_system_message(self, provider):
        mock_response = _make_text_response({"ok": True})

        with patch.object(
            provider._client, "post", new_callable=AsyncMock, return_value=mock_response
        ) as mock_post:
            await provider.generate(
                [
                    {"role": "system", "content": "You are helpful."},
                    {"role": "user", "content": "hi"},
                ]
            )

        call_body = mock_post.call_args[1]["json"]
        assert call_body["system"] == "You are helpful."
        assert all(m["role"] != "system" for m in call_body["messages"])

    async def test_http_error_raises_external_provider_error(self, provider):
        error_response = httpx.Response(
            429, json={"error": {"message": "rate limited"}}
        )

        with patch.object(
            provider._client,
            "post",
            new_callable=AsyncMock,
            return_value=error_response,
        ):
            with pytest.raises(ExternalProviderError, match="claude"):
                await provider.generate([{"role": "user", "content": "hello"}])

    async def test_invalid_json_raises_external_provider_error(self, provider):
        bad_response = httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": "not valid json{"}],
                "stop_reason": "end_turn",
            },
        )

        with patch.object(
            provider._client, "post", new_callable=AsyncMock, return_value=bad_response
        ):
            with pytest.raises(ExternalProviderError, match="claude"):
                await provider.generate([{"role": "user", "content": "hello"}])

    async def test_unexpected_content_type_raises(self, provider):
        bad_response = httpx.Response(
            200,
            json={
                "content": [{"type": "image", "source": {}}],
                "stop_reason": "end_turn",
            },
        )

        with patch.object(
            provider._client, "post", new_callable=AsyncMock, return_value=bad_response
        ):
            with pytest.raises(ExternalProviderError, match="claude"):
                await provider.generate([{"role": "user", "content": "hello"}])
