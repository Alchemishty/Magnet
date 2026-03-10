"""Tests for the FFmpeg assembler."""

from unittest.mock import MagicMock, patch

import pytest

from app.rendering.assembler import AssemblerError, assemble, probe_duration
from app.schemas.composition import Composition, CompositionLayer


def _video_layer(**overrides) -> CompositionLayer:
    defaults = {"type": "video", "start": 0, "end": 5, "asset_id": "clip_1"}
    return CompositionLayer(**(defaults | overrides))


def _audio_layer(**overrides) -> CompositionLayer:
    defaults = {
        "type": "audio",
        "start": 0,
        "end": 10,
        "asset_id": "audio_1",
        "volume": 0.8,
    }
    return CompositionLayer(**(defaults | overrides))


def _text_layer(**overrides) -> CompositionLayer:
    defaults = {
        "type": "text",
        "start": 0,
        "end": 3,
        "content": "Play Now!",
        "position": "top_center",
    }
    return CompositionLayer(**(defaults | overrides))


class TestAssembleCommand:
    @patch("app.rendering.assembler.subprocess.run")
    def test_video_only_composition(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr=b"")
        comp = Composition(
            duration=5,
            resolution=[1080, 1920],
            fps=30,
            layers=[_video_layer()],
        )
        asset_map = {"clip_1": "/tmp/clip_1.mp4"}
        result = assemble(comp, asset_map, "/tmp/output.mp4")

        assert result == "/tmp/output.mp4"
        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "ffmpeg"
        assert "/tmp/clip_1.mp4" in cmd

    @patch("app.rendering.assembler.subprocess.run")
    def test_audio_video_composition(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr=b"")
        comp = Composition(
            duration=10,
            resolution=[1080, 1920],
            fps=30,
            layers=[_video_layer(end=10), _audio_layer()],
        )
        asset_map = {
            "clip_1": "/tmp/clip_1.mp4",
            "audio_1": "/tmp/bg_music.wav",
        }
        assemble(comp, asset_map, "/tmp/output.mp4")

        cmd = mock_run.call_args[0][0]
        assert "/tmp/bg_music.wav" in cmd

    @patch("app.rendering.assembler.subprocess.run")
    def test_text_overlay(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr=b"")
        comp = Composition(
            duration=5,
            resolution=[1080, 1920],
            fps=30,
            layers=[_video_layer(), _text_layer()],
        )
        asset_map = {"clip_1": "/tmp/clip_1.mp4"}
        assemble(comp, asset_map, "/tmp/output.mp4")

        cmd_str = " ".join(mock_run.call_args[0][0])
        assert "drawtext" in cmd_str
        assert "Play Now!" in cmd_str

    @patch("app.rendering.assembler.subprocess.run")
    def test_trimmed_clip(self, mock_run):
        mock_run.return_value = MagicMock(returncode=0, stderr=b"")
        comp = Composition(
            duration=5,
            resolution=[1080, 1920],
            fps=30,
            layers=[_video_layer(trim=[10.0, 15.0])],
        )
        asset_map = {"clip_1": "/tmp/clip_1.mp4"}
        assemble(comp, asset_map, "/tmp/output.mp4")

        cmd_str = " ".join(mock_run.call_args[0][0])
        assert "trim" in cmd_str or "ss" in cmd_str


class TestAssembleErrors:
    @patch("app.rendering.assembler.subprocess.run")
    def test_nonzero_exit_raises(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1, stderr=b"Error: invalid input"
        )
        comp = Composition(
            duration=5,
            resolution=[1080, 1920],
            fps=30,
            layers=[_video_layer()],
        )
        with pytest.raises(AssemblerError, match="invalid input"):
            assemble(comp, {"clip_1": "/tmp/c.mp4"}, "/tmp/out.mp4")

    @patch("app.rendering.assembler.subprocess.run")
    def test_missing_asset_raises(self, mock_run):
        comp = Composition(
            duration=5,
            resolution=[1080, 1920],
            fps=30,
            layers=[_video_layer()],
        )
        with pytest.raises(AssemblerError, match="clip_1"):
            assemble(comp, {}, "/tmp/out.mp4")


class TestProbeDuration:
    @patch("app.rendering.assembler.subprocess.run")
    def test_returns_duration(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=0, stdout=b"12.500000\n", stderr=b""
        )
        duration = probe_duration("/tmp/file.mp4")
        assert duration == 12.5

    @patch("app.rendering.assembler.subprocess.run")
    def test_raises_on_failure(self, mock_run):
        mock_run.return_value = MagicMock(
            returncode=1, stdout=b"", stderr=b"not found"
        )
        with pytest.raises(AssemblerError):
            probe_duration("/tmp/missing.mp4")
