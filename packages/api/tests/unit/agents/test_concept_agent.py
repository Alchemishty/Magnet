"""Tests for the Concept Agent pipeline steps and orchestrator."""

from uuid import uuid4

import pytest

from app.agents.concept_agent import (
    ConceptAgent,
    ConceptAgentError,
    diversify,
    expand,
    strategize,
)
from app.schemas.brief import BriefCreate
from app.schemas.project import GameProfileRead
from tests.helpers.mocks import MockLLMProvider, MockLLMProviderError


def _make_game_profile(**overrides) -> GameProfileRead:
    """Create a GameProfileRead instance for testing."""
    defaults = {
        "id": uuid4(),
        "project_id": uuid4(),
        "genre": "puzzle",
        "target_audience": "casual gamers",
        "core_mechanics": ["match-3"],
        "art_style": "cartoon",
        "brand_guidelines": {},
        "competitors": ["Candy Crush"],
        "key_selling_points": ["addictive gameplay"],
        "created_at": "2026-01-01T00:00:00",
        "updated_at": None,
    }
    return GameProfileRead.model_validate(defaults | overrides)


CANNED_STRATEGIZE_RESPONSE = {
    "directions": [
        {
            "hook_type": "Fail/Challenge",
            "emotion": "curiosity",
            "angle": "Can you beat level 50?",
        },
        {
            "hook_type": "Satisfaction",
            "emotion": "relaxation",
            "angle": "Oddly satisfying match combos",
        },
    ],
}


def _make_expand_response(**overrides) -> dict:
    """Create a canned EXPAND LLM response."""
    defaults = {
        "hook_type": "Fail/Challenge",
        "narrative_angle": "Can you beat level 50?",
        "script": "Think you can solve this puzzle?",
        "voiceover_text": "Most players can't get past level 50.",
        "target_emotion": "curiosity",
        "cta_text": "Download now!",
        "target_format": "9:16",
        "target_duration": 15,
        "scene_plan": {
            "scenes": [
                {
                    "strategy": "RENDER",
                    "type": "text_hook",
                    "duration": 3,
                    "params": {"text": "Can YOU beat level 50?"},
                },
                {
                    "strategy": "COMPOSE",
                    "type": "gameplay",
                    "duration": 8,
                    "params": {"clip": "gameplay_1"},
                },
                {
                    "strategy": "GENERATE",
                    "type": "voiceover",
                    "duration": 4,
                    "params": {"voice": "energetic"},
                },
            ],
            "audio": {"music": "upbeat", "volume": 0.8},
        },
    }
    return defaults | overrides


class TestStrategize:
    async def test_returns_list_of_directions(self):
        mock = MockLLMProvider(response=CANNED_STRATEGIZE_RESPONSE)
        profile = _make_game_profile()

        result = await strategize(profile, mock)

        assert isinstance(result, list)
        assert len(result) == 2

    async def test_directions_have_required_keys(self):
        mock = MockLLMProvider(response=CANNED_STRATEGIZE_RESPONSE)
        profile = _make_game_profile()

        result = await strategize(profile, mock)

        for d in result:
            assert "hook_type" in d
            assert "emotion" in d
            assert "angle" in d

    async def test_passes_correct_messages_to_provider(self):
        mock = MockLLMProvider(response=CANNED_STRATEGIZE_RESPONSE)
        profile = _make_game_profile()

        await strategize(profile, mock)

        assert len(mock.calls) == 1
        messages = mock.calls[0]["messages"]
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert "puzzle" in messages[1]["content"]

    async def test_passes_schema_to_provider(self):
        mock = MockLLMProvider(response=CANNED_STRATEGIZE_RESPONSE)
        profile = _make_game_profile()

        await strategize(profile, mock)

        assert mock.calls[0]["schema"] is not None
        assert "directions" in str(mock.calls[0]["schema"])

    async def test_malformed_response_raises_error(self):
        mock = MockLLMProvider(response={"bad": "data"})
        profile = _make_game_profile()

        with pytest.raises(ConceptAgentError):
            await strategize(profile, mock)

    async def test_missing_keys_in_direction_raises_error(self):
        bad_response = {
            "directions": [
                {"hook_type": "Fail/Challenge"}
            ]
        }
        mock = MockLLMProvider(response=bad_response)
        profile = _make_game_profile()

        with pytest.raises(ConceptAgentError):
            await strategize(profile, mock)


class TestExpand:
    async def test_returns_list_of_brief_creates(self):
        directions = [
            {
                "hook_type": "Fail/Challenge",
                "emotion": "curiosity",
                "angle": "Can you beat level 50?",
            },
        ]
        mock = MockLLMProvider(response=_make_expand_response())
        profile = _make_game_profile()

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
        mock = MockLLMProvider(response=_make_expand_response())
        profile = _make_game_profile()

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
        mock = MockLLMProvider(response=_make_expand_response())
        profile = _make_game_profile()

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
            _make_expand_response(hook_type="Fail/Challenge"),
            _make_expand_response(hook_type="Satisfaction"),
            _make_expand_response(hook_type="Comparison"),
        ]
        mock = MockLLMProvider(responses=responses)
        profile = _make_game_profile()

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
            _make_expand_response(),
            _make_expand_response(hook_type="Satisfaction"),
        ]
        mock = MockLLMProvider(responses=responses)
        profile = _make_game_profile()

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
        profile = _make_game_profile()

        with pytest.raises(ConceptAgentError):
            await expand(profile, directions, mock)


def _make_test_briefs(count: int = 3) -> list[BriefCreate]:
    """Create a list of BriefCreate instances for testing."""
    hook_types = [
        "Fail/Challenge",
        "Satisfaction",
        "Comparison",
    ]
    angles = [
        "Can you beat this?",
        "So satisfying to watch",
        "Noob vs Pro",
    ]
    return [
        BriefCreate(
            project_id=uuid4(),
            hook_type=hook_types[i % len(hook_types)],
            narrative_angle=angles[i % len(angles)],
            script=f"Script {i}",
            target_emotion="curiosity",
            cta_text="Download now!",
            scene_plan={
                "scenes": [
                    {
                        "strategy": "COMPOSE",
                        "type": "gameplay",
                        "duration": 10,
                    }
                ]
            },
            status="draft",
            generated_by="agent",
        )
        for i in range(count)
    ]


class TestDiversify:
    async def test_keeps_briefs_at_keep_indices(self):
        briefs = _make_test_briefs(3)
        response = {
            "keep": [0, 2],
            "mutate": [],
            "drop": [1],
        }
        mock = MockLLMProvider(response=response)

        result = await diversify(briefs, mock)

        assert len(result) == 2
        assert result[0].hook_type == "Fail/Challenge"
        assert result[1].hook_type == "Comparison"

    async def test_mutates_briefs_at_mutate_indices(self):
        briefs = _make_test_briefs(3)
        response = {
            "keep": [0],
            "mutate": [
                {
                    "index": 1,
                    "mutation": "hook_type:Emotional",
                },
            ],
            "drop": [2],
        }
        mock = MockLLMProvider(response=response)

        result = await diversify(briefs, mock)

        assert len(result) == 2
        mutated = result[1]
        assert mutated.hook_type == "Emotional"

    async def test_mutates_narrative_angle(self):
        briefs = _make_test_briefs(2)
        response = {
            "keep": [],
            "mutate": [
                {
                    "index": 0,
                    "mutation": "narrative_angle:A fresh take",
                },
            ],
            "drop": [1],
        }
        mock = MockLLMProvider(response=response)

        result = await diversify(briefs, mock)

        assert len(result) == 1
        assert result[0].narrative_angle == "A fresh take"

    async def test_drops_briefs_at_drop_indices(self):
        briefs = _make_test_briefs(3)
        response = {
            "keep": [0],
            "mutate": [],
            "drop": [1, 2],
        }
        mock = MockLLMProvider(response=response)

        result = await diversify(briefs, mock)

        assert len(result) == 1
        assert result[0].hook_type == "Fail/Challenge"

    async def test_all_kept_no_mutations(self):
        briefs = _make_test_briefs(3)
        response = {
            "keep": [0, 1, 2],
            "mutate": [],
            "drop": [],
        }
        mock = MockLLMProvider(response=response)

        result = await diversify(briefs, mock)

        assert len(result) == 3

    async def test_out_of_range_index_raises_error(self):
        briefs = _make_test_briefs(2)
        response = {
            "keep": [0, 5],
            "mutate": [],
            "drop": [],
        }
        mock = MockLLMProvider(response=response)

        with pytest.raises(ConceptAgentError):
            await diversify(briefs, mock)

    async def test_malformed_response_raises_error(self):
        briefs = _make_test_briefs(2)
        mock = MockLLMProvider(response={"bad": "data"})

        with pytest.raises(ConceptAgentError):
            await diversify(briefs, mock)

    async def test_passes_schema_to_provider(self):
        briefs = _make_test_briefs(2)
        response = {
            "keep": [0, 1],
            "mutate": [],
            "drop": [],
        }
        mock = MockLLMProvider(response=response)

        await diversify(briefs, mock)

        assert mock.calls[0]["schema"] is not None


class TestConceptAgent:
    def _build_full_responses(
        self, num_directions: int = 2
    ) -> list[dict]:
        """Build sequential responses for the full pipeline.

        Order: 1 strategize + N expand + 1 diversify.
        """
        strategize_resp = {
            "directions": [
                {
                    "hook_type": "Fail/Challenge",
                    "emotion": "curiosity",
                    "angle": f"Direction {i}",
                }
                for i in range(num_directions)
            ],
        }

        expand_resps = [
            _make_expand_response(
                hook_type="Fail/Challenge",
                narrative_angle=f"Angle {i}",
            )
            for i in range(num_directions)
        ]

        diversify_resp = {
            "keep": list(range(num_directions)),
            "mutate": [],
            "drop": [],
        }

        return [strategize_resp, *expand_resps, diversify_resp]

    async def test_full_pipeline_returns_briefs(self):
        responses = self._build_full_responses(num_directions=2)
        mock = MockLLMProvider(responses=responses)
        agent = ConceptAgent(llm=mock)
        profile = _make_game_profile()

        result = await agent.generate_briefs(profile)

        assert isinstance(result, list)
        assert all(isinstance(b, BriefCreate) for b in result)
        assert len(result) == 2

    async def test_correct_number_of_llm_calls(self):
        num_directions = 3
        responses = self._build_full_responses(
            num_directions=num_directions
        )
        mock = MockLLMProvider(responses=responses)
        agent = ConceptAgent(llm=mock)
        profile = _make_game_profile()

        await agent.generate_briefs(profile)

        # 1 strategize + N expand + 1 diversify
        expected_calls = 1 + num_directions + 1
        assert len(mock.calls) == expected_calls

    async def test_strategize_error_prevents_expand(self):
        mock = MockLLMProvider(response={"bad": "data"})
        agent = ConceptAgent(llm=mock)
        profile = _make_game_profile()

        with pytest.raises(ConceptAgentError):
            await agent.generate_briefs(profile)

        # Only 1 call (strategize) should have been made
        assert len(mock.calls) == 1

    async def test_provider_error_propagates(self):
        error_mock = MockLLMProviderError(
            error=RuntimeError("LLM down")
        )
        agent = ConceptAgent(llm=error_mock)
        profile = _make_game_profile()

        with pytest.raises(RuntimeError, match="LLM down"):
            await agent.generate_briefs(profile)
