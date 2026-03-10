"""ElevenLabs TTS provider."""

import httpx

from app.errors import ExternalProviderError

_BASE_URL = "https://api.elevenlabs.io"
_DEFAULT_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # "Rachel" — ElevenLabs default


class ElevenLabsProvider:
    """TTSProvider implementation backed by the ElevenLabs API."""

    def __init__(self, api_key: str, default_voice: str = _DEFAULT_VOICE_ID):
        self._default_voice = default_voice
        self._client = httpx.AsyncClient(
            base_url=_BASE_URL,
            headers={
                "xi-api-key": api_key,
                "content-type": "application/json",
            },
            timeout=60.0,
        )

    async def aclose(self) -> None:
        await self._client.aclose()

    async def synthesize(self, text: str, voice: str | None = None) -> bytes:
        voice_id = voice or self._default_voice
        response = await self._client.post(
            f"/v1/text-to-speech/{voice_id}",
            json={
                "text": text,
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75,
                },
            },
        )

        if response.status_code != 200:
            detail = _extract_error_detail(response)
            raise ExternalProviderError("elevenlabs", detail)

        return response.content


def _extract_error_detail(response: httpx.Response) -> str:
    try:
        body = response.json()
        if isinstance(body, dict):
            detail = body.get("detail", {})
            if isinstance(detail, dict):
                return detail.get("message", response.text)
            return str(detail)
        return response.text
    except Exception:
        return f"HTTP {response.status_code}: {response.text}"
