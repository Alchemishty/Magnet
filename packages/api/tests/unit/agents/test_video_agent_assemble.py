"""Tests for the Video Agent ASSEMBLE and POST-PROCESS phases."""

import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.agents.video_agent import VideoAgent
from app.schemas.execution_plan import ExecutionPlan, PreparedAudio, PreparedScene
from app.schemas.scene_plan import Scene, ScenePlan


def _make_agent():
    return VideoAgent(
        tts_provider=MagicMock(),
        music_provider=MagicMock(),
        image_provider=MagicMock(),
        asset_repo=MagicMock(),
    )


class TestAssemblePhase:
    def test_builds_composition_from_ready_scenes(self):
        agent = _make_agent()
        plan = ExecutionPlan(
            brief_id=uuid4(),
            project_id=uuid4(),
            scenes=[
                PreparedScene(index=0, strategy="GENERATE", status="ready",
                              output_path="/tmp/scene_0.mp4"),
                PreparedScene(index=1, strategy="RENDER", status="ready",
                              output_path="/tmp/scene_1.mp4"),
            ],
            work_dir="/tmp/work",
        )
        scene_plan = ScenePlan(scenes=[
            Scene(strategy="GENERATE", type="hook", duration=3.0, prompt="x"),
            Scene(strategy="RENDER", type="endcard", duration=2.0,
                  template="endcard"),
        ])

        comp = agent.assemble(plan, scene_plan)

        assert comp.duration == 5.0
        assert comp.resolution == [1080, 1920]
        video_layers = [ly for ly in comp.layers if ly.type == "video"]
        assert len(video_layers) == 2
        assert video_layers[0].start == 0
        assert video_layers[0].end == 3.0
        assert video_layers[1].start == 3.0
        assert video_layers[1].end == 5.0

    def test_skips_failed_scenes(self):
        agent = _make_agent()
        plan = ExecutionPlan(
            brief_id=uuid4(),
            project_id=uuid4(),
            scenes=[
                PreparedScene(index=0, strategy="GENERATE", status="failed",
                              error_message="broke"),
                PreparedScene(index=1, strategy="RENDER", status="ready",
                              output_path="/tmp/scene_1.mp4"),
            ],
            work_dir="/tmp/work",
        )
        scene_plan = ScenePlan(scenes=[
            Scene(strategy="GENERATE", type="hook", duration=3.0, prompt="x"),
            Scene(strategy="RENDER", type="endcard", duration=2.0,
                  template="endcard"),
        ])

        comp = agent.assemble(plan, scene_plan)

        video_layers = [ly for ly in comp.layers if ly.type == "video"]
        assert len(video_layers) == 1
        assert comp.duration == 2.0

    def test_includes_audio_layers(self):
        agent = _make_agent()
        plan = ExecutionPlan(
            brief_id=uuid4(),
            project_id=uuid4(),
            scenes=[
                PreparedScene(index=0, strategy="RENDER", status="ready",
                              output_path="/tmp/scene_0.mp4"),
            ],
            audio=[
                PreparedAudio(type="voiceover", status="ready",
                              output_path="/tmp/voiceover.mp3"),
                PreparedAudio(type="music", status="ready",
                              output_path="/tmp/music.wav"),
            ],
            work_dir="/tmp/work",
        )
        scene_plan = ScenePlan(scenes=[
            Scene(strategy="RENDER", type="hook", duration=5.0,
                  template="text_hook"),
        ])

        comp = agent.assemble(plan, scene_plan)

        audio_layers = [ly for ly in comp.layers if ly.type == "audio"]
        assert len(audio_layers) == 2
        assert audio_layers[0].asset_id == "voiceover"
        assert audio_layers[1].asset_id == "music"


class TestBuildAndRender:
    @patch("app.agents.video_agent.assembler_assemble")
    def test_calls_assembler(self, mock_assemble):
        mock_assemble.return_value = "/tmp/output.mp4"
        agent = _make_agent()
        plan = ExecutionPlan(
            brief_id=uuid4(),
            project_id=uuid4(),
            scenes=[
                PreparedScene(index=0, strategy="RENDER", status="ready",
                              output_path="/tmp/scene_0.mp4"),
            ],
            work_dir="/tmp/work",
        )
        scene_plan = ScenePlan(scenes=[
            Scene(strategy="RENDER", type="hook", duration=5.0,
                  template="text_hook"),
        ])
        comp = agent.assemble(plan, scene_plan)

        result = agent.build_and_render(comp, plan)

        assert result == "/tmp/output.mp4"
        mock_assemble.assert_called_once()


class TestPostProcess:
    @pytest.mark.asyncio
    @patch("app.agents.video_agent.boto3")
    async def test_uploads_to_s3(self, mock_boto3):
        mock_client = MagicMock()
        mock_boto3.client.return_value = mock_client

        agent = _make_agent()
        work_dir = tempfile.mkdtemp()
        output_path = os.path.join(work_dir, "output.mp4")
        with open(output_path, "wb") as f:
            f.write(b"fake_video")

        with patch.dict("os.environ", {
            "S3_ENDPOINT": "http://localhost:9000",
            "S3_ACCESS_KEY": "key",
            "S3_SECRET_KEY": "secret",
            "S3_BUCKET": "magnet-assets",
        }):
            s3_key = await agent.post_process(output_path, "job-123")

        assert s3_key == "renders/job-123/output.mp4"
        mock_client.upload_file.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_local_path_when_s3_not_configured(self):
        agent = _make_agent()
        work_dir = tempfile.mkdtemp()
        output_path = os.path.join(work_dir, "output.mp4")
        with open(output_path, "wb") as f:
            f.write(b"fake_video")

        with patch.dict("os.environ", {}, clear=True):
            os.environ.pop("S3_BUCKET", None)
            result = await agent.post_process(output_path, "job-456")

        assert result == output_path


class TestProduce:
    @pytest.mark.asyncio
    @patch("app.agents.video_agent.boto3")
    @patch("app.agents.video_agent.assembler_assemble")
    async def test_full_pipeline(self, mock_assemble, mock_boto3):
        mock_assemble.return_value = "/tmp/work/output.mp4"
        mock_boto3.client.return_value = MagicMock()

        agent = _make_agent()
        agent._image.generate = AsyncMock(return_value=b"image_data")
        agent._asset_repo.list_by_project.return_value = []

        brief_id = uuid4()
        brief = MagicMock()
        brief.id = brief_id
        brief.project_id = uuid4()
        brief.scene_plan = {
            "scenes": [
                {"strategy": "GENERATE", "type": "hook", "duration": 3.0,
                 "prompt": "shocked face"},
            ],
        }

        work_dir = tempfile.mkdtemp()

        with patch.dict("os.environ", {
            "S3_ENDPOINT": "http://localhost:9000",
            "S3_ACCESS_KEY": "key",
            "S3_SECRET_KEY": "secret",
            "S3_BUCKET": "magnet-assets",
        }):
            s3_key, composition = await agent.produce(brief, work_dir)

        assert s3_key is not None
        assert composition is not None
        mock_assemble.assert_called_once()
