"""Tests for MockLLMProvider and MockLLMProviderError."""

import pytest

from tests.helpers.mocks import MockLLMProvider, MockLLMProviderError


class TestMockLLMProvider:
    async def test_records_calls(self):
        mock = MockLLMProvider(response={"result": "ok"})
        messages = [{"role": "user", "content": "hello"}]
        schema = {"type": "object"}

        await mock.generate(messages, schema=schema)

        assert len(mock.calls) == 1
        assert mock.calls[0]["messages"] == messages
        assert mock.calls[0]["schema"] == schema

    async def test_returns_single_response(self):
        expected = {"directions": [{"hook_type": "Fail/Challenge"}]}
        mock = MockLLMProvider(response=expected)

        result = await mock.generate([{"role": "user", "content": "hi"}])

        assert result == expected

    async def test_returns_same_response_on_multiple_calls(self):
        expected = {"result": "ok"}
        mock = MockLLMProvider(response=expected)

        r1 = await mock.generate([{"role": "user", "content": "1"}])
        r2 = await mock.generate([{"role": "user", "content": "2"}])

        assert r1 == expected
        assert r2 == expected
        assert len(mock.calls) == 2

    async def test_returns_sequential_responses(self):
        responses = [{"step": 1}, {"step": 2}, {"step": 3}]
        mock = MockLLMProvider(responses=responses)

        r1 = await mock.generate([{"role": "user", "content": "1"}])
        r2 = await mock.generate([{"role": "user", "content": "2"}])
        r3 = await mock.generate([{"role": "user", "content": "3"}])

        assert r1 == {"step": 1}
        assert r2 == {"step": 2}
        assert r3 == {"step": 3}

    async def test_cycles_when_responses_exhausted(self):
        responses = [{"a": 1}, {"b": 2}]
        mock = MockLLMProvider(responses=responses)

        await mock.generate([{"role": "user", "content": "1"}])
        await mock.generate([{"role": "user", "content": "2"}])
        r3 = await mock.generate([{"role": "user", "content": "3"}])

        assert r3 == {"a": 1}

    async def test_schema_defaults_to_none(self):
        mock = MockLLMProvider(response={"ok": True})

        await mock.generate([{"role": "user", "content": "hi"}])

        assert mock.calls[0]["schema"] is None


class TestMockLLMProviderError:
    async def test_raises_specified_exception(self):
        error = RuntimeError("LLM failed")
        mock = MockLLMProviderError(error=error)

        with pytest.raises(RuntimeError, match="LLM failed"):
            await mock.generate(
                [{"role": "user", "content": "hi"}]
            )

    async def test_raises_on_every_call(self):
        error = ValueError("bad input")
        mock = MockLLMProviderError(error=error)

        with pytest.raises(ValueError):
            await mock.generate([{"role": "user", "content": "1"}])

        with pytest.raises(ValueError):
            await mock.generate([{"role": "user", "content": "2"}])
