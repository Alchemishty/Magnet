"""Tests for the stub image provider."""

from io import BytesIO

import pytest
from PIL import Image

from app.providers.image.stub import StubImageProvider


@pytest.fixture
def provider():
    return StubImageProvider()


class TestGenerate:
    @pytest.mark.asyncio
    async def test_returns_bytes(self, provider):
        result = await provider.generate("a hero image", 200, 300)
        assert isinstance(result, bytes)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_returns_valid_png(self, provider):
        result = await provider.generate("scene image", 100, 100)
        img = Image.open(BytesIO(result))
        assert img.format == "PNG"

    @pytest.mark.asyncio
    async def test_dimensions_match_request(self, provider):
        result = await provider.generate("test", 320, 480)
        img = Image.open(BytesIO(result))
        assert img.size == (320, 480)

    @pytest.mark.asyncio
    async def test_same_prompt_produces_same_color(self, provider):
        r1 = await provider.generate("a sunset", 10, 10)
        r2 = await provider.generate("a sunset", 10, 10)
        assert r1 == r2

    @pytest.mark.asyncio
    async def test_different_prompts_produce_different_colors(self, provider):
        r1 = await provider.generate("a sunset", 10, 10)
        r2 = await provider.generate("a forest", 10, 10)
        assert r1 != r2


class TestAclose:
    @pytest.mark.asyncio
    async def test_aclose_is_noop(self, provider):
        await provider.aclose()


class TestFactory:
    def test_factory_returns_stub(self):
        from app.providers.image import get_image_provider

        provider = get_image_provider()
        assert isinstance(provider, StubImageProvider)
