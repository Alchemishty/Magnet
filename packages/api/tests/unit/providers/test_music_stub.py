"""Tests for the stub music provider."""

import wave
from io import BytesIO

import pytest

from app.providers.music.stub import StubMusicProvider


@pytest.fixture
def provider():
    return StubMusicProvider()


class TestGenerate:
    @pytest.mark.asyncio
    async def test_returns_bytes(self, provider):
        result = await provider.generate("upbeat music", 5)
        assert isinstance(result, bytes)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_returns_valid_wav(self, provider):
        result = await provider.generate("background music", 3)
        buf = BytesIO(result)
        with wave.open(buf, "rb") as wf:
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2
            assert wf.getframerate() == 44100

    @pytest.mark.asyncio
    async def test_duration_matches_request(self, provider):
        result = await provider.generate("music", 2)
        buf = BytesIO(result)
        with wave.open(buf, "rb") as wf:
            actual_duration = wf.getnframes() / wf.getframerate()
            assert abs(actual_duration - 2.0) < 0.1


class TestAclose:
    @pytest.mark.asyncio
    async def test_aclose_is_noop(self, provider):
        await provider.aclose()


class TestFactory:
    def test_factory_returns_stub(self):
        from app.providers.music import get_music_provider

        provider = get_music_provider()
        assert isinstance(provider, StubMusicProvider)
