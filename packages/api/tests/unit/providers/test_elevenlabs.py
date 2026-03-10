"""Tests for the ElevenLabs TTS provider."""

from unittest.mock import AsyncMock

import httpx
import pytest

from app.providers.tts.elevenlabs import ElevenLabsProvider


@pytest.fixture
def provider():
    return ElevenLabsProvider(api_key="test-key")


@pytest.fixture
def provider_with_voice():
    return ElevenLabsProvider(api_key="test-key", default_voice="custom-voice")


class TestSynthesize:
    @pytest.mark.asyncio
    async def test_returns_audio_bytes(self, provider):
        audio_bytes = b"\xff\xfb\x90\x00" * 100
        mock_response = httpx.Response(200, content=audio_bytes)
        provider._client.post = AsyncMock(return_value=mock_response)

        result = await provider.synthesize("Hello world", "voice-123")

        assert result == audio_bytes
        provider._client.post.assert_called_once()
        call_args = provider._client.post.call_args
        assert "voice-123" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_uses_default_voice_when_voice_is_none(self, provider_with_voice):
        audio_bytes = b"\xff\xfb\x90\x00"
        mock_response = httpx.Response(200, content=audio_bytes)
        provider_with_voice._client.post = AsyncMock(return_value=mock_response)

        result = await provider_with_voice.synthesize("Hello", None)

        assert result == audio_bytes
        call_url = provider_with_voice._client.post.call_args[0][0]
        assert "custom-voice" in call_url

    @pytest.mark.asyncio
    async def test_raises_on_api_error(self, provider):
        mock_response = httpx.Response(
            401, json={"detail": {"message": "Unauthorized"}}
        )
        provider._client.post = AsyncMock(return_value=mock_response)

        from app.errors import ExternalProviderError

        with pytest.raises(ExternalProviderError, match="elevenlabs"):
            await provider.synthesize("Hello", "voice-123")

    @pytest.mark.asyncio
    async def test_sends_correct_request_body(self, provider):
        mock_response = httpx.Response(200, content=b"audio")
        provider._client.post = AsyncMock(return_value=mock_response)

        await provider.synthesize("Test text", "voice-id")

        call_kwargs = provider._client.post.call_args
        body = call_kwargs[1]["json"]
        assert body["text"] == "Test text"


class TestAclose:
    @pytest.mark.asyncio
    async def test_closes_client(self, provider):
        provider._client.aclose = AsyncMock()
        await provider.aclose()
        provider._client.aclose.assert_called_once()
