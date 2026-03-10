"""Tests for execution plan schemas."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.execution_plan import ExecutionPlan, PreparedAudio, PreparedScene


class TestPreparedScene:
    def test_defaults(self):
        scene = PreparedScene(index=0, strategy="COMPOSE")
        assert scene.status == "pending"
        assert scene.output_path is None
        assert scene.error_message is None

    def test_ready_scene(self):
        scene = PreparedScene(
            index=1,
            strategy="GENERATE",
            status="ready",
            output_path="/tmp/work/scene_1.mp4",
        )
        assert scene.status == "ready"
        assert scene.output_path == "/tmp/work/scene_1.mp4"

    def test_failed_scene(self):
        scene = PreparedScene(
            index=2,
            strategy="RENDER",
            status="failed",
            error_message="Template not found",
        )
        assert scene.status == "failed"
        assert scene.error_message == "Template not found"

    def test_invalid_status_raises(self):
        with pytest.raises(ValidationError):
            PreparedScene(index=0, strategy="COMPOSE", status="unknown")

    def test_invalid_strategy_raises(self):
        with pytest.raises(ValidationError):
            PreparedScene(index=0, strategy="INVALID")


class TestPreparedAudio:
    def test_voiceover(self):
        audio = PreparedAudio(type="voiceover")
        assert audio.status == "pending"

    def test_music(self):
        audio = PreparedAudio(type="music", status="ready", output_path="/tmp/bg.wav")
        assert audio.output_path == "/tmp/bg.wav"

    def test_invalid_type_raises(self):
        with pytest.raises(ValidationError):
            PreparedAudio(type="sfx")


class TestExecutionPlan:
    def test_minimal_plan(self):
        brief_id = uuid4()
        plan = ExecutionPlan(
            brief_id=brief_id,
            scenes=[PreparedScene(index=0, strategy="COMPOSE")],
            work_dir="/tmp/work",
        )
        assert plan.brief_id == brief_id
        assert len(plan.scenes) == 1
        assert len(plan.audio) == 0
        assert plan.work_dir == "/tmp/work"

    def test_plan_with_audio(self):
        plan = ExecutionPlan(
            brief_id=uuid4(),
            scenes=[PreparedScene(index=0, strategy="GENERATE")],
            audio=[
                PreparedAudio(type="voiceover"),
                PreparedAudio(type="music"),
            ],
            work_dir="/tmp/work",
        )
        assert len(plan.audio) == 2

    def test_empty_scenes_raises(self):
        with pytest.raises(ValidationError):
            ExecutionPlan(
                brief_id=uuid4(),
                scenes=[],
                work_dir="/tmp/work",
            )
