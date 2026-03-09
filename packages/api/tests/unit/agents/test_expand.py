"""Tests for the EXPAND pipeline step."""

import pytest

from app.agents.concept_agent import ConceptAgentError, expand
from app.schemas.brief import BriefCreate
from tests.helpers.mocks import MockLLMProvider
from tests.unit.agents.conftest import (
    make_expand_response,
    make_game_profile,
)


class TestExpand:
    async def test_returns_list_of_brief_creates(self):
        directions = [
            {
                "hook_type": "Fail/Challenge",
                "emotion": "curiosity",
                "angle": "Can you beat level 50?",
            },
        ]
        mock = MockLLMProvider(response=make_expand_response())
        profile = make_game_profile()

        result = await expand(profile, directions, mock)

        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], BriefCreate)

    async def test_brief_has_correct_fields(self):
        directions = [
            {
                "hook_type": "Fail/Challenge",
                "emotion": "curiosity",
                "angle": "test",
            },
        ]
        mock = MockLLMProvider(response=make_expand_response())
        profile = make_game_profile()

        result = await expand(profile, directions, mock)

        brief = result[0]
        assert brief.hook_type == "Fail/Challenge"
        assert brief.narrative_angle == "Can you beat level 50?"
        assert brief.generated_by == "agent"
        assert brief.status == "draft"
        assert brief.scene_plan is not None
        assert "scenes" in brief.scene_plan

    async def test_scene_plan_has_strategy_tags(self):
        directions = [
            {
                "hook_type": "Fail/Challenge",
                "emotion": "curiosity",
                "angle": "test",
            },
        ]
        mock = MockLLMProvider(response=make_expand_response())
        profile = make_game_profile()

        result = await expand(profile, directions, mock)

        scenes = result[0].scene_plan["scenes"]
        strategies = {s["strategy"] for s in scenes}
        assert strategies == {"RENDER", "COMPOSE", "GENERATE"}

    async def test_expands_multiple_directions(self):
        directions = [
            {
                "hook_type": "Fail/Challenge",
                "emotion": "curiosity",
                "angle": "test1",
            },
            {
                "hook_type": "Satisfaction",
                "emotion": "relaxation",
                "angle": "test2",
            },
            {
                "hook_type": "Comparison",
                "emotion": "competition",
                "angle": "test3",
            },
        ]
        responses = [
            make_expand_response(hook_type="Fail/Challenge"),
            make_expand_response(hook_type="Satisfaction"),
            make_expand_response(hook_type="Comparison"),
        ]
        mock = MockLLMProvider(responses=responses)
        profile = make_game_profile()

        result = await expand(profile, directions, mock)

        assert len(result) == 3
        assert len(mock.calls) == 3
        assert result[0].hook_type == "Fail/Challenge"
        assert result[1].hook_type == "Satisfaction"
        assert result[2].hook_type == "Comparison"

    async def test_each_call_gets_correct_direction(self):
        directions = [
            {
                "hook_type": "Fail/Challenge",
                "emotion": "curiosity",
                "angle": "angle one",
            },
            {
                "hook_type": "Satisfaction",
                "emotion": "relaxation",
                "angle": "angle two",
            },
        ]
        responses = [
            make_expand_response(),
            make_expand_response(hook_type="Satisfaction"),
        ]
        mock = MockLLMProvider(responses=responses)
        profile = make_game_profile()

        await expand(profile, directions, mock)

        msg1 = mock.calls[0]["messages"][1]["content"]
        msg2 = mock.calls[1]["messages"][1]["content"]
        assert "angle one" in msg1
        assert "angle two" in msg2

    async def test_malformed_response_raises_error(self):
        directions = [
            {
                "hook_type": "Fail/Challenge",
                "emotion": "curiosity",
                "angle": "test",
            },
        ]
        mock = MockLLMProvider(response={"bad": "data"})
        profile = make_game_profile()

        with pytest.raises(ConceptAgentError):
            await expand(profile, directions, mock)
