"""Stub image provider — generates solid-color PNG images."""

import hashlib
from io import BytesIO

from PIL import Image


class StubImageProvider:
    """ImageProvider stub that returns a solid-color PNG based on the prompt hash."""

    async def generate(self, prompt: str, width: int, height: int) -> bytes:
        color = _color_from_prompt(prompt)
        img = Image.new("RGB", (width, height), color)
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    async def aclose(self) -> None:
        pass


def _color_from_prompt(prompt: str) -> tuple[int, int, int]:
    digest = hashlib.md5(prompt.encode()).digest()
    return (digest[0], digest[1], digest[2])
