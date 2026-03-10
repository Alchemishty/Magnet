"""Tests for the TTS provider factory."""

from unittest.mock import patch

import pytest

from app.providers.tts import get_tts_provider
from app.providers.tts.elevenlabs import ElevenLabsProvider


class TestGetTtsProvider:
    @patch.dict("os.environ", {"ELEVENLABS_API_KEY": "test-key"})
    def test_returns_elevenlabs_by_default(self):
        provider = get_tts_provider()
        assert isinstance(provider, ElevenLabsProvider)

    @patch.dict("os.environ", {"TTS_PROVIDER": "elevenlabs", "ELEVENLABS_API_KEY": "k"})
    def test_returns_elevenlabs_explicitly(self):
        provider = get_tts_provider()
        assert isinstance(provider, ElevenLabsProvider)

    @patch.dict("os.environ", {"TTS_PROVIDER": "elevenlabs"}, clear=False)
    def test_raises_on_missing_api_key(self):
        import os

        os.environ.pop("ELEVENLABS_API_KEY", None)
        with pytest.raises(ValueError, match="ELEVENLABS_API_KEY"):
            get_tts_provider()

    @patch.dict("os.environ", {"TTS_PROVIDER": "unknown"})
    def test_raises_on_unknown_provider(self):
        with pytest.raises(ValueError, match="Unknown TTS_PROVIDER"):
            get_tts_provider()

    @patch.dict(
        "os.environ",
        {
            "ELEVENLABS_API_KEY": "k",
            "ELEVENLABS_DEFAULT_VOICE": "my-voice",
        },
    )
    def test_passes_default_voice_from_env(self):
        provider = get_tts_provider()
        assert provider._default_voice == "my-voice"
