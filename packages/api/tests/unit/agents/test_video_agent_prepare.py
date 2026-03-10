"""Tests for the Video Agent PREPARE phase."""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.agents.video_agent import VideoAgent, VideoAgentError
from app.schemas.execution_plan import ExecutionPlan, PreparedAudio, PreparedScene
from app.schemas.scene_plan import (
    AudioPlan,
    MusicPlan,
    Scene,
    ScenePlan,
    VoiceoverPlan,
)


def _make_agent(tts_bytes=b"audio", music_bytes=b"music", image_bytes=b"image"):
    tts = MagicMock()
    tts.synthesize = AsyncMock(return_value=tts_bytes)
    music = MagicMock()
    music.generate = AsyncMock(return_value=music_bytes)
    image = MagicMock()
    image.generate = AsyncMock(return_value=image_bytes)
    asset_repo = MagicMock()
    asset_repo.list_by_project.return_value = []
    return VideoAgent(
        tts_provider=tts,
        music_provider=music,
        image_provider=image,
        asset_repo=asset_repo,
    )


class TestPrepareGenerate:
    @pytest.mark.asyncio
    async def test_generate_scene_calls_image_provider(self):
        agent = _make_agent(image_bytes=b"\x89PNG_fake")
        plan = ExecutionPlan(
            brief_id=uuid4(),
            project_id=uuid4(),
            scenes=[PreparedScene(index=0, strategy="GENERATE")],
            work_dir=tempfile.mkdtemp(),
        )
        scene_plan = ScenePlan(scenes=[
            Scene(strategy="GENERATE", type="hook", duration=2.0,
                  generator="image_gen", prompt="shocked face"),
        ])

        result = await agent.prepare(plan, scene_plan)

        assert result.scenes[0].status == "ready"
        assert result.scenes[0].output_path is not None
        assert os.path.exists(result.scenes[0].output_path)
        agent._image.generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_scene_writes_file(self):
        agent = _make_agent(image_bytes=b"fake_image_data")
        work_dir = tempfile.mkdtemp()
        plan = ExecutionPlan(
            brief_id=uuid4(),
            project_id=uuid4(),
            scenes=[PreparedScene(index=0, strategy="GENERATE")],
            work_dir=work_dir,
        )
        scene_plan = ScenePlan(scenes=[
            Scene(strategy="GENERATE", type="hook", duration=2.0,
                  prompt="shocked face"),
        ])

        result = await agent.prepare(plan, scene_plan)

        with open(result.scenes[0].output_path, "rb") as f:
            assert f.read() == b"fake_image_data"


class TestPrepareRender:
    @pytest.mark.asyncio
    @patch("app.agents.video_agent.get_template")
    async def test_render_scene_calls_template(self, mock_get_template):
        mock_renderer = MagicMock()
        mock_renderer.render.return_value = b"video_bytes"
        mock_get_template.return_value = mock_renderer

        agent = _make_agent()
        plan = ExecutionPlan(
            brief_id=uuid4(),
            project_id=uuid4(),
            scenes=[PreparedScene(index=0, strategy="RENDER")],
            work_dir=tempfile.mkdtemp(),
        )
        scene_plan = ScenePlan(scenes=[
            Scene(strategy="RENDER", type="fake_gameplay", duration=3.0,
                  template="text_hook", params={"text": "Test"}),
        ])

        result = await agent.prepare(plan, scene_plan)

        assert result.scenes[0].status == "ready"
        mock_get_template.assert_called_once_with("text_hook")
        mock_renderer.render.assert_called_once()


class TestPrepareAudio:
    @pytest.mark.asyncio
    async def test_voiceover_calls_tts(self):
        agent = _make_agent(tts_bytes=b"tts_audio")
        plan = ExecutionPlan(
            brief_id=uuid4(),
            project_id=uuid4(),
            scenes=[PreparedScene(index=0, strategy="RENDER")],
            audio=[PreparedAudio(type="voiceover")],
            work_dir=tempfile.mkdtemp(),
        )
        scene_plan = ScenePlan(
            scenes=[Scene(strategy="RENDER", type="hook", duration=2.0,
                          template="text_hook", params={"text": "Hi"})],
            audio=AudioPlan(
                voiceover=VoiceoverPlan(
                    generator="elevenlabs",
                    script="Download now!", voice="v1",
                ),
            ),
        )

        result = await agent.prepare(plan, scene_plan)

        assert result.audio[0].status == "ready"
        assert result.audio[0].output_path is not None
        agent._tts.synthesize.assert_called_once_with("Download now!", "v1")

    @pytest.mark.asyncio
    async def test_music_calls_provider(self):
        agent = _make_agent(music_bytes=b"music_data")
        plan = ExecutionPlan(
            brief_id=uuid4(),
            project_id=uuid4(),
            scenes=[PreparedScene(index=0, strategy="RENDER")],
            audio=[PreparedAudio(type="music")],
            work_dir=tempfile.mkdtemp(),
        )
        scene_plan = ScenePlan(
            scenes=[Scene(strategy="RENDER", type="hook", duration=5.0,
                          template="text_hook", params={"text": "Hi"})],
            audio=AudioPlan(
                music=MusicPlan(
                    generator="suno",
                    prompt="upbeat game music",
                ),
            ),
        )

        result = await agent.prepare(plan, scene_plan)

        assert result.audio[0].status == "ready"
        agent._music.generate.assert_called_once()


class TestPreparePartialFailure:
    @pytest.mark.asyncio
    @patch("app.agents.video_agent.get_template")
    async def test_one_scene_fails_others_succeed(self, mock_get_template):
        mock_renderer = MagicMock()
        mock_renderer.render.side_effect = [RuntimeError("template broke"), b"ok"]
        mock_get_template.return_value = mock_renderer

        agent = _make_agent()
        plan = ExecutionPlan(
            brief_id=uuid4(),
            project_id=uuid4(),
            scenes=[
                PreparedScene(index=0, strategy="RENDER"),
                PreparedScene(index=1, strategy="RENDER"),
            ],
            work_dir=tempfile.mkdtemp(),
        )
        scene_plan = ScenePlan(scenes=[
            Scene(strategy="RENDER", type="hook", duration=2.0,
                  template="text_hook", params={"text": "A"}),
            Scene(strategy="RENDER", type="endcard", duration=2.0,
                  template="text_hook", params={"text": "B"}),
        ])

        result = await agent.prepare(plan, scene_plan)

        assert result.scenes[0].status == "failed"
        assert "template broke" in result.scenes[0].error_message
        assert result.scenes[1].status == "ready"

    @pytest.mark.asyncio
    @patch("app.agents.video_agent.get_template")
    async def test_all_scenes_fail_raises(self, mock_get_template):
        mock_renderer = MagicMock()
        mock_renderer.render.side_effect = RuntimeError("broken")
        mock_get_template.return_value = mock_renderer

        agent = _make_agent()
        plan = ExecutionPlan(
            brief_id=uuid4(),
            project_id=uuid4(),
            scenes=[PreparedScene(index=0, strategy="RENDER")],
            work_dir=tempfile.mkdtemp(),
        )
        scene_plan = ScenePlan(scenes=[
            Scene(strategy="RENDER", type="hook", duration=2.0,
                  template="text_hook", params={"text": "Fail"}),
        ])

        with pytest.raises(VideoAgentError, match="All scenes failed"):
            await agent.prepare(plan, scene_plan)
