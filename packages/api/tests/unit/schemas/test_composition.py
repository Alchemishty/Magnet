"""Tests for the Composition schema."""

import pytest
from pydantic import ValidationError

from app.schemas.composition import Composition, CompositionLayer


class TestCompositionLayer:
    def test_valid_video_layer(self):
        layer = CompositionLayer(
            type="video",
            start=0,
            end=8,
            asset_id="asset_123",
        )

        assert layer.type == "video"
        assert layer.start == 0
        assert layer.end == 8

    def test_valid_text_layer(self):
        layer = CompositionLayer(
            type="text",
            start=0,
            end=3,
            content="Can you beat level 50?",
            position="top_center",
            animation="fade_in",
        )

        assert layer.content == "Can you beat level 50?"

    def test_valid_audio_layer(self):
        layer = CompositionLayer(
            type="audio",
            start=0,
            end=15,
            asset_id="asset_456",
            volume=0.8,
        )

        assert layer.volume == 0.8

    def test_rejects_invalid_type(self):
        with pytest.raises(ValidationError):
            CompositionLayer(type="invalid", start=0, end=5)

    def test_position_accepts_list(self):
        layer = CompositionLayer(type="video", start=0, end=5, position=[0, 100])

        assert layer.position == [0, 100]

    def test_position_accepts_string(self):
        layer = CompositionLayer(type="video", start=0, end=5, position="center")

        assert layer.position == "center"


class TestComposition:
    def test_valid_composition(self):
        comp = Composition(
            duration=15,
            resolution=[1080, 1920],
            fps=30,
            layers=[
                CompositionLayer(
                    type="video",
                    start=0,
                    end=8,
                    asset_id="asset_123",
                ),
                CompositionLayer(
                    type="text",
                    start=0,
                    end=3,
                    content="Hello",
                ),
            ],
        )

        assert comp.duration == 15
        assert comp.resolution == [1080, 1920]
        assert len(comp.layers) == 2

    def test_fps_defaults_to_30(self):
        comp = Composition(
            duration=15,
            resolution=[1080, 1920],
            layers=[],
        )

        assert comp.fps == 30

    def test_rejects_missing_duration(self):
        with pytest.raises(ValidationError):
            Composition(resolution=[1080, 1920], layers=[])

    def test_rejects_missing_resolution(self):
        with pytest.raises(ValidationError):
            Composition(duration=15, layers=[])

    def test_full_design_doc_example(self):
        comp = Composition(
            duration=15,
            resolution=[1080, 1920],
            fps=30,
            layers=[
                CompositionLayer(
                    type="video",
                    asset_id="asset_123",
                    start=0,
                    end=8,
                    trim=[12.5, 20.5],
                    position=[0, 0],
                    effects=["zoom_in_slow"],
                ),
                CompositionLayer(
                    type="text",
                    content="Can you beat level 50?",
                    start=0,
                    end=3,
                    position="top_center",
                    animation="fade_in",
                ),
                CompositionLayer(
                    type="audio",
                    asset_id="asset_456",
                    start=0,
                    end=15,
                    volume=0.8,
                ),
            ],
        )

        assert len(comp.layers) == 3
        assert comp.layers[0].trim == [12.5, 20.5]
        assert comp.layers[2].volume == 0.8
