"""Claude LLM provider using the Anthropic Messages API."""

import json

import httpx

from app.errors import ExternalProviderError

_DEFAULT_MODEL = "claude-sonnet-4-20250514"
_BASE_URL = "https://api.anthropic.com"
_API_VERSION = "2023-06-01"
_MAX_TOKENS = 4096


class ClaudeProvider:
    """LLMProvider implementation backed by the Anthropic Messages API."""

    def __init__(self, api_key: str, model: str = _DEFAULT_MODEL):
        self._model = model
        self._client = httpx.AsyncClient(
            base_url=_BASE_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": _API_VERSION,
                "content-type": "application/json",
            },
            timeout=120.0,
        )

    async def generate(self, messages: list[dict], schema: dict | None = None) -> dict:
        system = None
        filtered: list[dict] = []
        for m in messages:
            if m["role"] == "system":
                system = m["content"]
            else:
                filtered.append(m)

        body: dict = {
            "model": self._model,
            "max_tokens": _MAX_TOKENS,
            "messages": filtered,
        }
        if system:
            body["system"] = system

        if schema is not None:
            body["tools"] = [
                {
                    "name": "structured_output",
                    "description": "Return structured data matching the schema.",
                    "input_schema": schema,
                }
            ]
            body["tool_choice"] = {
                "type": "tool",
                "name": "structured_output",
            }

        response = await self._client.post("/v1/messages", json=body)

        if response.status_code != 200:
            detail = _extract_error_detail(response)
            raise ExternalProviderError("claude", detail)

        data = response.json()
        return _parse_response(data, schema is not None)


def _extract_error_detail(response: httpx.Response) -> str:
    try:
        body = response.json()
        return body.get("error", {}).get("message", response.text)
    except Exception:
        return f"HTTP {response.status_code}: {response.text}"


def _parse_response(data: dict, expect_tool_use: bool) -> dict:
    content = data.get("content")
    if not isinstance(content, list) or len(content) == 0:
        raise ExternalProviderError("claude", "Empty content in response")

    block = content[0]

    if expect_tool_use:
        if block.get("type") != "tool_use":
            raise ExternalProviderError(
                "claude",
                f"Expected tool_use block, got '{block.get('type')}'",
            )
        result = block.get("input")
        if not isinstance(result, dict):
            raise ExternalProviderError("claude", "Tool use block has no input dict")
        return result

    if block.get("type") != "text":
        raise ExternalProviderError(
            "claude",
            f"Expected text block, got '{block.get('type')}'",
        )

    try:
        return json.loads(block["text"])
    except (json.JSONDecodeError, KeyError) as e:
        raise ExternalProviderError(
            "claude", f"Failed to parse JSON from response: {e}"
        ) from e
