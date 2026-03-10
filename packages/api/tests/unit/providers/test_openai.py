"""Tests for OpenAIProvider."""

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from app.errors import ExternalProviderError
from app.providers.llm.openai import OpenAIProvider


@pytest.fixture
def provider():
    return OpenAIProvider(api_key="test-key")


def _make_response(content: dict) -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": json.dumps(content),
                    },
                    "finish_reason": "stop",
                }
            ],
        },
    )


class TestOpenAIProviderInit:
    def test_default_model(self, provider):
        assert provider._model == "gpt-4o"

    def test_custom_model(self):
        p = OpenAIProvider(api_key="k", model="gpt-4o-mini")
        assert p._model == "gpt-4o-mini"

    def test_sets_auth_header(self, provider):
        headers = provider._client.headers
        assert headers["authorization"] == "Bearer test-key"


class TestOpenAIProviderLifecycle:
    async def test_aclose_closes_client(self, provider):
        with patch.object(
            provider._client, "aclose", new_callable=AsyncMock
        ) as mock_close:
            await provider.aclose()
            mock_close.assert_called_once()


class TestOpenAIProviderGenerate:
    async def test_without_schema_returns_parsed_json(self, provider):
        expected = {"directions": [{"hook_type": "Fail"}]}
        mock_response = _make_response(expected)

        with patch.object(
            provider._client, "post", new_callable=AsyncMock, return_value=mock_response
        ):
            result = await provider.generate([{"role": "user", "content": "hello"}])

        assert result == expected

    async def test_with_schema_sends_json_schema_format(self, provider):
        expected = {"directions": []}
        mock_response = _make_response(expected)
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
        assert call_body["response_format"]["type"] == "json_schema"
        assert call_body["response_format"]["json_schema"]["schema"] == schema

    async def test_passes_messages_directly(self, provider):
        mock_response = _make_response({"ok": True})
        schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}}

        with patch.object(
            provider._client, "post", new_callable=AsyncMock, return_value=mock_response
        ) as mock_post:
            await provider.generate(
                [
                    {"role": "system", "content": "Be helpful."},
                    {"role": "user", "content": "hi"},
                ],
                schema=schema,
            )

        call_body = mock_post.call_args[1]["json"]
        assert call_body["messages"][0] == {
            "role": "system",
            "content": "Be helpful.",
        }

    async def test_http_error_raises_external_provider_error(self, provider):
        error_response = httpx.Response(
            500, json={"error": {"message": "server error"}}
        )

        with patch.object(
            provider._client,
            "post",
            new_callable=AsyncMock,
            return_value=error_response,
        ):
            with pytest.raises(ExternalProviderError, match="openai"):
                await provider.generate([{"role": "user", "content": "hello"}])

    async def test_invalid_json_raises_external_provider_error(self, provider):
        bad_response = httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "not json{",
                        },
                        "finish_reason": "stop",
                    }
                ],
            },
        )

        with patch.object(
            provider._client, "post", new_callable=AsyncMock, return_value=bad_response
        ):
            with pytest.raises(ExternalProviderError, match="openai"):
                await provider.generate([{"role": "user", "content": "hello"}])

    async def test_empty_choices_raises(self, provider):
        bad_response = httpx.Response(200, json={"choices": []})

        with patch.object(
            provider._client, "post", new_callable=AsyncMock, return_value=bad_response
        ):
            with pytest.raises(ExternalProviderError, match="openai"):
                await provider.generate([{"role": "user", "content": "hello"}])
