"""TTS provider factory — selects the active provider from env vars."""

import os

from app.providers.tts.elevenlabs import ElevenLabsProvider

_PROVIDERS = {
    "elevenlabs": ("ELEVENLABS_API_KEY", ElevenLabsProvider),
}


def get_tts_provider() -> ElevenLabsProvider:
    """Create a TTS provider instance from environment configuration.

    Reads:
        TTS_PROVIDER — "elevenlabs" (default)
        ELEVENLABS_API_KEY — required for elevenlabs
        ELEVENLABS_DEFAULT_VOICE — optional voice ID override
    """
    provider_name = os.environ.get("TTS_PROVIDER", "elevenlabs")

    if provider_name not in _PROVIDERS:
        raise ValueError(
            f"Unknown TTS_PROVIDER '{provider_name}'. "
            f"Supported: {sorted(_PROVIDERS)}"
        )

    key_env, provider_cls = _PROVIDERS[provider_name]
    api_key = os.environ.get(key_env)
    if not api_key:
        raise ValueError(
            f"{key_env} environment variable is required "
            f"when TTS_PROVIDER={provider_name}"
        )

    kwargs: dict = {"api_key": api_key}
    default_voice = os.environ.get("ELEVENLABS_DEFAULT_VOICE")
    if default_voice:
        kwargs["default_voice"] = default_voice

    return provider_cls(**kwargs)
