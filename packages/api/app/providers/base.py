from typing import Protocol


class LLMProvider(Protocol):
    async def generate(self, messages: list[dict], schema: dict | None = None) -> dict: ...


class TTSProvider(Protocol):
    async def synthesize(self, text: str, voice: str) -> bytes: ...


class MusicProvider(Protocol):
    async def generate(self, prompt: str, duration: int) -> bytes: ...


class ImageProvider(Protocol):
    async def generate(self, prompt: str, width: int, height: int) -> bytes: ...


class VideoProvider(Protocol):
    async def generate(self, prompt: str, duration: int) -> bytes: ...
