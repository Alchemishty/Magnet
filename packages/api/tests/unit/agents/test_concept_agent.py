"""Tests for the Concept Agent pipeline steps and orchestrator."""

from uuid import uuid4

import pytest

from app.agents.concept_agent import ConceptAgentError, strategize
from app.schemas.project import GameProfileRead
from tests.helpers.mocks import MockLLMProvider


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
                {"hook_type": "Fail/Challenge"}  # missing emotion, angle
            ]
        }
        mock = MockLLMProvider(response=bad_response)
        profile = _make_game_profile()

        with pytest.raises(ConceptAgentError):
            await strategize(profile, mock)
