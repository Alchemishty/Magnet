"""Tests for the ConceptAgent orchestrator."""

import pytest

from app.agents.concept_agent import ConceptAgent, ConceptAgentError
from app.schemas.brief import BriefCreate
from tests.helpers.mocks import MockLLMProvider, MockLLMProviderError
from tests.unit.agents.conftest import (
    make_expand_response,
    make_game_profile,
)


class TestConceptAgent:
    def _build_full_responses(self, num_directions: int = 2) -> list[dict]:
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
            make_expand_response(
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
        profile = make_game_profile()

        result = await agent.generate_briefs(profile)

        assert isinstance(result, list)
        assert all(isinstance(b, BriefCreate) for b in result)
        assert len(result) == 2

    async def test_correct_number_of_llm_calls(self):
        num_directions = 3
        responses = self._build_full_responses(num_directions=num_directions)
        mock = MockLLMProvider(responses=responses)
        agent = ConceptAgent(llm=mock)
        profile = make_game_profile()

        await agent.generate_briefs(profile)

        # 1 strategize + N expand + 1 diversify
        expected_calls = 1 + num_directions + 1
        assert len(mock.calls) == expected_calls

    async def test_strategize_error_prevents_expand(self):
        mock = MockLLMProvider(response={"bad": "data"})
        agent = ConceptAgent(llm=mock)
        profile = make_game_profile()

        with pytest.raises(ConceptAgentError):
            await agent.generate_briefs(profile)

        # Only 1 call (strategize) should have been made
        assert len(mock.calls) == 1

    async def test_provider_error_propagates(self):
        error_mock = MockLLMProviderError(error=RuntimeError("LLM down"))
        agent = ConceptAgent(llm=error_mock)
        profile = make_game_profile()

        with pytest.raises(RuntimeError, match="LLM down"):
            await agent.generate_briefs(profile)
