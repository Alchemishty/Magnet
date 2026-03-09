"""Mock providers for testing."""


class MockLLMProvider:
    """Mock LLM provider that records calls and returns canned responses.

    Satisfies the LLMProvider protocol from app.providers.base.
    """

    def __init__(
        self,
        response: dict | None = None,
        responses: list[dict] | None = None,
    ):
        if response is not None and responses is not None:
            msg = "Provide response or responses, not both"
            raise ValueError(msg)

        if response is not None:
            self._responses = [response]
        elif responses is not None:
            if len(responses) == 0:
                msg = "responses must not be empty"
                raise ValueError(msg)
            self._responses = list(responses)
        else:
            msg = "Provide either response or responses"
            raise ValueError(msg)

        self._call_index = 0
        self.calls: list[dict] = []

    async def generate(
        self,
        messages: list[dict],
        schema: dict | None = None,
    ) -> dict:
        self.calls.append({"messages": messages, "schema": schema})
        idx = self._call_index % len(self._responses)
        self._call_index += 1
        return self._responses[idx]


class MockLLMProviderError:
    """Mock LLM provider that raises a specified exception."""

    def __init__(self, error: Exception):
        self._error = error

    async def generate(
        self,
        messages: list[dict],
        schema: dict | None = None,
    ) -> dict:
        raise self._error
