"""Tests for the text hook template renderer."""

from unittest.mock import MagicMock, patch

import pytest

from app.rendering.templates.text_hook import TextHookRenderer


@pytest.fixture
def renderer():
    return TextHookRenderer()


class TestGenerateFrames:
    def test_produces_correct_frame_count(self, renderer):
        frames = renderer.generate_frames(
            params={"text": "Can you beat this?"},
            duration=1.0,
            resolution=(100, 100),
            fps=10,
        )
        assert len(frames) == 10

    def test_frames_are_pil_images(self, renderer):
        from PIL import Image

        frames = renderer.generate_frames(
            params={"text": "Test"},
            duration=1.0,
            resolution=(100, 100),
            fps=10,
        )
        for frame in frames:
            assert isinstance(frame, Image.Image)
            assert frame.size == (100, 100)

    def test_missing_text_raises(self, renderer):
        with pytest.raises(ValueError, match="text"):
            renderer.generate_frames(
                params={},
                duration=1.0,
                resolution=(100, 100),
                fps=10,
            )

    def test_custom_font_accepted(self, renderer):
        frames = renderer.generate_frames(
            params={"text": "Hello", "font": "/nonexistent/font.ttf"},
            duration=0.5,
            resolution=(100, 100),
            fps=10,
        )
        assert len(frames) == 5


class TestRender:
    @patch("app.rendering.templates.base.subprocess.run")
    def test_render_calls_ffmpeg(self, mock_run, renderer):
        mock_run.return_value = MagicMock(returncode=0, stderr=b"", stdout=b"\x00\x00")
        result = renderer.render(
            params={"text": "Test hook"},
            duration=1.0,
            resolution=(100, 100),
            fps=10,
        )
        assert isinstance(result, bytes)
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert "ffmpeg" in cmd[0]
