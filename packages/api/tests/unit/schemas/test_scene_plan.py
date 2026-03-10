"""Tests for scene plan schemas."""

import pytest
from pydantic import ValidationError

from app.schemas.scene_plan import AudioPlan, Scene, ScenePlan, VoiceoverPlan, MusicPlan


class TestScene:
    def test_compose_scene(self):
        scene = Scene(
            strategy="COMPOSE",
            type="real_gameplay",
            duration=5.0,
            asset_query="gameplay footage, most action-dense segment",
        )
        assert scene.strategy == "COMPOSE"
        assert scene.type == "real_gameplay"
        assert scene.duration == 5.0
        assert scene.asset_query == "gameplay footage, most action-dense segment"

    def test_generate_scene(self):
        scene = Scene(
            strategy="GENERATE",
            type="hook",
            duration=2.0,
            generator="heygen",
            prompt="Young woman looking at phone, shocked expression",
        )
        assert scene.strategy == "GENERATE"
        assert scene.generator == "heygen"
        assert scene.prompt == "Young woman looking at phone, shocked expression"

    def test_render_scene(self):
        scene = Scene(
            strategy="RENDER",
            type="fake_gameplay",
            duration=4.0,
            template="pin_pull_fail",
            params={"difficulty": "obvious_fail", "theme": "water"},
        )
        assert scene.strategy == "RENDER"
        assert scene.template == "pin_pull_fail"
        assert scene.params == {"difficulty": "obvious_fail", "theme": "water"}

    def test_scene_with_font(self):
        scene = Scene(
            strategy="RENDER",
            type="hook",
            duration=2.0,
            template="text_hook",
            font="/path/to/custom.ttf",
        )
        assert scene.font == "/path/to/custom.ttf"

    def test_invalid_strategy_raises(self):
        with pytest.raises(ValidationError):
            Scene(strategy="INVALID", type="hook", duration=2.0)

    def test_missing_duration_raises(self):
        with pytest.raises(ValidationError):
            Scene(strategy="COMPOSE", type="real_gameplay")

    def test_negative_duration_raises(self):
        with pytest.raises(ValidationError):
            Scene(strategy="COMPOSE", type="real_gameplay", duration=-1.0)


class TestAudioPlan:
    def test_voiceover_only(self):
        audio = AudioPlan(
            voiceover=VoiceoverPlan(
                strategy="GENERATE",
                generator="elevenlabs",
                script="Download now!",
            )
        )
        assert audio.voiceover is not None
        assert audio.voiceover.script == "Download now!"
        assert audio.music is None

    def test_voiceover_with_custom_voice(self):
        audio = AudioPlan(
            voiceover=VoiceoverPlan(
                strategy="GENERATE",
                generator="elevenlabs",
                script="Try it now!",
                voice="custom-voice-id-123",
            )
        )
        assert audio.voiceover.voice == "custom-voice-id-123"

    def test_music_only(self):
        audio = AudioPlan(
            music=MusicPlan(
                strategy="GENERATE",
                generator="suno",
                prompt="upbeat casual game background music",
            )
        )
        assert audio.music is not None
        assert audio.voiceover is None

    def test_both_voiceover_and_music(self):
        audio = AudioPlan(
            voiceover=VoiceoverPlan(
                strategy="GENERATE", generator="elevenlabs", script="Play now!"
            ),
            music=MusicPlan(
                strategy="GENERATE", generator="suno", prompt="upbeat music"
            ),
        )
        assert audio.voiceover is not None
        assert audio.music is not None


class TestScenePlan:
    def test_valid_scene_plan(self):
        plan = ScenePlan(
            scenes=[
                Scene(strategy="GENERATE", type="hook", duration=2.0, prompt="shock"),
                Scene(strategy="COMPOSE", type="real_gameplay", duration=5.0),
            ]
        )
        assert len(plan.scenes) == 2
        assert plan.audio is None

    def test_scene_plan_with_audio(self):
        plan = ScenePlan(
            scenes=[Scene(strategy="COMPOSE", type="endcard", duration=2.0)],
            audio=AudioPlan(
                voiceover=VoiceoverPlan(
                    strategy="GENERATE", generator="elevenlabs", script="Go!"
                )
            ),
        )
        assert plan.audio is not None

    def test_empty_scenes_raises(self):
        with pytest.raises(ValidationError):
            ScenePlan(scenes=[])

    def test_missing_scenes_raises(self):
        with pytest.raises(ValidationError):
            ScenePlan()
