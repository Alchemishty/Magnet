"""Tests for the endcard template renderer."""

from unittest.mock import MagicMock, patch

import pytest

from app.rendering.templates.endcard import EndcardRenderer


@pytest.fixture
def renderer():
    return EndcardRenderer()


class TestGenerateFrames:
    def test_produces_correct_frame_count(self, renderer):
        frames = renderer.generate_frames(
            params={"cta_text": "Download Now!"},
            duration=1.0,
            resolution=(100, 100),
            fps=10,
        )
        assert len(frames) == 10

    def test_frames_are_pil_images(self, renderer):
        from PIL import Image

        frames = renderer.generate_frames(
            params={"cta_text": "Play Free"},
            duration=1.0,
            resolution=(100, 100),
            fps=10,
        )
        for frame in frames:
            assert isinstance(frame, Image.Image)

    def test_missing_cta_text_raises(self, renderer):
        with pytest.raises(ValueError, match="cta_text"):
            renderer.generate_frames(
                params={},
                duration=1.0,
                resolution=(100, 100),
                fps=10,
            )

    def test_with_game_name(self, renderer):
        frames = renderer.generate_frames(
            params={"cta_text": "Download", "game_name": "Puzzle Quest"},
            duration=1.0,
            resolution=(100, 100),
            fps=10,
        )
        assert len(frames) == 10


class TestRender:
    @patch("app.rendering.templates.base.subprocess.run")
    def test_render_calls_ffmpeg(self, mock_run, renderer):
        mock_run.return_value = MagicMock(returncode=0, stderr=b"", stdout=b"\x00\x00")
        result = renderer.render(
            params={"cta_text": "Get it now!"},
            duration=1.0,
            resolution=(100, 100),
            fps=10,
        )
        assert isinstance(result, bytes)
        mock_run.assert_called_once()


class TestTemplateRegistry:
    def test_get_text_hook(self):
        from app.rendering.templates import get_template
        from app.rendering.templates.text_hook import TextHookRenderer

        t = get_template("text_hook")
        assert isinstance(t, TextHookRenderer)

    def test_get_endcard(self):
        from app.rendering.templates import get_template
        from app.rendering.templates.endcard import EndcardRenderer

        t = get_template("endcard")
        assert isinstance(t, EndcardRenderer)

    def test_unknown_template_raises(self):
        from app.rendering.templates import get_template

        with pytest.raises(ValueError, match="Unknown template"):
            get_template("nonexistent")
