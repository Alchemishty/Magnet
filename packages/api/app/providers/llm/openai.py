"""OpenAI LLM provider using the Chat Completions API."""

import json

import httpx

from app.errors import ExternalProviderError

_DEFAULT_MODEL = "gpt-4o"
_BASE_URL = "https://api.openai.com/v1"


class OpenAIProvider:
    """LLMProvider implementation backed by the OpenAI Chat Completions API."""

    def __init__(self, api_key: str, model: str = _DEFAULT_MODEL):
        self._model = model
        self._client = httpx.AsyncClient(
            base_url=_BASE_URL,
            headers={
                "authorization": f"Bearer {api_key}",
                "content-type": "application/json",
            },
            timeout=120.0,
        )

    async def generate(self, messages: list[dict], schema: dict | None = None) -> dict:
        body: dict = {
            "model": self._model,
            "messages": list(messages),
        }

        if schema is not None:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": {
                    "name": "response",
                    "strict": True,
                    "schema": schema,
                },
            }
        else:
            body["response_format"] = {"type": "json_object"}
            body["messages"] = _ensure_json_instruction(body["messages"])

        response = await self._client.post("/chat/completions", json=body)

        if response.status_code != 200:
            detail = _extract_error_detail(response)
            raise ExternalProviderError("openai", detail)

        data = response.json()
        return _parse_response(data)


def _ensure_json_instruction(messages: list[dict]) -> list[dict]:
    """Ensure at least one message mentions JSON for json_object mode."""
    for m in messages:
        if "json" in m.get("content", "").lower():
            return messages
    return [
        {"role": "system", "content": "Respond with valid JSON."},
        *messages,
    ]


def _extract_error_detail(response: httpx.Response) -> str:
    try:
        body = response.json()
        return body.get("error", {}).get("message", response.text)
    except Exception:
        return f"HTTP {response.status_code}: {response.text}"


def _parse_response(data: dict) -> dict:
    choices = data.get("choices")
    if not isinstance(choices, list) or len(choices) == 0:
        raise ExternalProviderError("openai", "Empty choices in response")

    content = choices[0].get("message", {}).get("content")
    if not isinstance(content, str):
        raise ExternalProviderError("openai", "No content in response message")

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        raise ExternalProviderError(
            "openai", f"Failed to parse JSON from response: {e}"
        ) from e
