"""Tests for the Video Agent PLAN phase."""

from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.agents.video_agent import VideoAgent, VideoAgentError
from app.schemas.brief import BriefRead


def _make_brief(**overrides) -> BriefRead:
    defaults = {
        "id": uuid4(),
        "project_id": uuid4(),
        "hook_type": "fail_challenge",
        "narrative_angle": "Can you beat this?",
        "script": "Think you can do better?",
        "voiceover_text": None,
        "target_emotion": "curiosity",
        "cta_text": "Download now!",
        "reference_ads": [],
        "target_format": "9:16",
        "target_duration": 15,
        "status": "approved",
        "generated_by": "agent",
        "scene_plan": None,
        "created_at": "2026-03-10T00:00:00",
        "updated_at": None,
    }
    return BriefRead(**(defaults | overrides))


def _make_agent(assets=None):
    tts = MagicMock()
    music = MagicMock()
    image = MagicMock()
    asset_repo = MagicMock()
    if assets is not None:
        asset_repo.list_by_project.return_value = assets
    else:
        asset_repo.list_by_project.return_value = []
    return VideoAgent(
        tts_provider=tts,
        music_provider=music,
        image_provider=image,
        asset_repo=asset_repo,
    )


class TestPlanPhase:
    def test_plan_with_generate_scenes(self):
        brief = _make_brief(
            scene_plan={
                "scenes": [
                    {
                        "strategy": "GENERATE",
                        "type": "hook",
                        "duration": 2.0,
                        "generator": "heygen",
                        "prompt": "shocked face",
                    },
                    {
                        "strategy": "RENDER",
                        "type": "fake_gameplay",
                        "duration": 4.0,
                        "template": "text_hook",
                        "params": {"text": "Can you beat this?"},
                    },
                ]
            }
        )
        agent = _make_agent()
        plan = agent.plan(brief, "/tmp/work")

        assert plan.brief_id == brief.id
        assert len(plan.scenes) == 2
        assert plan.scenes[0].strategy == "GENERATE"
        assert plan.scenes[1].strategy == "RENDER"
        assert all(s.status == "pending" for s in plan.scenes)
        assert plan.work_dir == "/tmp/work"

    def test_plan_with_audio(self):
        brief = _make_brief(
            scene_plan={
                "scenes": [
                    {"strategy": "RENDER", "type": "hook", "duration": 2.0,
                     "template": "text_hook"},
                ],
                "audio": {
                    "voiceover": {
                        "strategy": "GENERATE",
                        "generator": "elevenlabs",
                        "script": "Download now!",
                    },
                    "music": {
                        "strategy": "GENERATE",
                        "generator": "suno",
                        "prompt": "upbeat music",
                    },
                },
            }
        )
        agent = _make_agent()
        plan = agent.plan(brief, "/tmp/work")

        assert len(plan.audio) == 2
        types = {a.type for a in plan.audio}
        assert types == {"voiceover", "music"}

    def test_plan_with_compose_scene_and_assets(self):
        mock_asset = MagicMock()
        mock_asset.s3_key = "uploads/gameplay.mp4"
        mock_asset.asset_type = "gameplay"
        brief = _make_brief(
            scene_plan={
                "scenes": [
                    {
                        "strategy": "COMPOSE",
                        "type": "real_gameplay",
                        "duration": 5.0,
                        "asset_query": "gameplay footage",
                    },
                ]
            }
        )
        agent = _make_agent(assets=[mock_asset])
        plan = agent.plan(brief, "/tmp/work")

        assert len(plan.scenes) == 1
        assert plan.scenes[0].strategy == "COMPOSE"

    def test_plan_missing_scene_plan_raises(self):
        brief = _make_brief(scene_plan=None)
        agent = _make_agent()

        with pytest.raises(VideoAgentError, match="scene_plan"):
            agent.plan(brief, "/tmp/work")

    def test_plan_empty_scenes_raises(self):
        brief = _make_brief(scene_plan={"scenes": []})
        agent = _make_agent()

        with pytest.raises(VideoAgentError):
            agent.plan(brief, "/tmp/work")

    def test_plan_compose_no_assets_raises(self):
        brief = _make_brief(
            scene_plan={
                "scenes": [
                    {
                        "strategy": "COMPOSE",
                        "type": "real_gameplay",
                        "duration": 5.0,
                    },
                ]
            }
        )
        agent = _make_agent(assets=[])

        with pytest.raises(VideoAgentError, match="No assets"):
            agent.plan(brief, "/tmp/work")

    def test_plan_mixed_strategies(self):
        mock_asset = MagicMock()
        mock_asset.s3_key = "uploads/gameplay.mp4"
        brief = _make_brief(
            scene_plan={
                "scenes": [
                    {"strategy": "GENERATE", "type": "hook", "duration": 2.0,
                     "prompt": "wow"},
                    {"strategy": "COMPOSE", "type": "real_gameplay",
                     "duration": 5.0},
                    {"strategy": "RENDER", "type": "endcard", "duration": 2.0,
                     "template": "endcard"},
                ]
            }
        )
        agent = _make_agent(assets=[mock_asset])
        plan = agent.plan(brief, "/tmp/work")

        assert len(plan.scenes) == 3
        strategies = [s.strategy for s in plan.scenes]
        assert strategies == ["GENERATE", "COMPOSE", "RENDER"]
