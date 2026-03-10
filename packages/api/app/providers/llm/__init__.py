"""LLM provider factory — selects the active provider from env vars."""

import os

from app.providers.llm.claude import ClaudeProvider
from app.providers.llm.openai import OpenAIProvider

_PROVIDERS = {
    "claude": ("ANTHROPIC_API_KEY", ClaudeProvider),
    "openai": ("OPENAI_API_KEY", OpenAIProvider),
}


def get_llm_provider() -> ClaudeProvider | OpenAIProvider:
    """Create an LLM provider instance from environment configuration.

    Reads:
        LLM_PROVIDER — "claude" (default) or "openai"
        ANTHROPIC_API_KEY / OPENAI_API_KEY — required for the chosen provider
        LLM_MODEL — optional model override
    """
    provider_name = os.environ.get("LLM_PROVIDER", "claude")

    if provider_name not in _PROVIDERS:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{provider_name}'. "
            f"Supported: {sorted(_PROVIDERS)}"
        )

    key_env, provider_cls = _PROVIDERS[provider_name]
    api_key = os.environ.get(key_env)
    if not api_key:
        raise ValueError(
            f"{key_env} environment variable is required "
            f"when LLM_PROVIDER={provider_name}"
        )

    kwargs: dict = {"api_key": api_key}
    model = os.environ.get("LLM_MODEL")
    if model:
        kwargs["model"] = model

    return provider_cls(**kwargs)
