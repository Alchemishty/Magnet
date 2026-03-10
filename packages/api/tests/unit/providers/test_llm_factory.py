"""Tests for LLM provider factory."""

import pytest

from app.providers.llm import get_llm_provider
from app.providers.llm.claude import ClaudeProvider
from app.providers.llm.openai import OpenAIProvider


class TestGetLLMProvider:
    def test_returns_claude_by_default(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.delenv("LLM_PROVIDER", raising=False)

        provider = get_llm_provider()

        assert isinstance(provider, ClaudeProvider)

    def test_returns_claude_when_explicit(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "claude")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

        provider = get_llm_provider()

        assert isinstance(provider, ClaudeProvider)

    def test_returns_openai(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        provider = get_llm_provider()

        assert isinstance(provider, OpenAIProvider)

    def test_custom_model_override(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "claude")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("LLM_MODEL", "claude-haiku-4-5-20251001")

        provider = get_llm_provider()

        assert isinstance(provider, ClaudeProvider)
        assert provider._model == "claude-haiku-4-5-20251001"

    def test_raises_on_unknown_provider(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "gemini")

        with pytest.raises(ValueError, match="gemini"):
            get_llm_provider()

    def test_raises_on_missing_claude_key(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "claude")
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
            get_llm_provider()

    def test_raises_on_missing_openai_key(self, monkeypatch):
        monkeypatch.setenv("LLM_PROVIDER", "openai")
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with pytest.raises(ValueError, match="OPENAI_API_KEY"):
            get_llm_provider()
