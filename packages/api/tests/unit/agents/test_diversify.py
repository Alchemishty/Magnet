"""Tests for the DIVERSIFY pipeline step."""

import pytest

from app.agents.concept_agent import ConceptAgentError, diversify
from tests.helpers.mocks import MockLLMProvider
from tests.unit.agents.conftest import make_test_briefs


class TestDiversify:
    async def test_keeps_briefs_at_keep_indices(self):
        briefs = make_test_briefs(3)
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
        briefs = make_test_briefs(3)
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
        briefs = make_test_briefs(2)
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
        briefs = make_test_briefs(3)
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
        briefs = make_test_briefs(3)
        response = {
            "keep": [0, 1, 2],
            "mutate": [],
            "drop": [],
        }
        mock = MockLLMProvider(response=response)

        result = await diversify(briefs, mock)

        assert len(result) == 3

    async def test_out_of_range_index_raises_error(self):
        briefs = make_test_briefs(2)
        response = {
            "keep": [0, 5],
            "mutate": [],
            "drop": [],
        }
        mock = MockLLMProvider(response=response)

        with pytest.raises(ConceptAgentError):
            await diversify(briefs, mock)

    async def test_malformed_response_raises_error(self):
        briefs = make_test_briefs(2)
        mock = MockLLMProvider(response={"bad": "data"})

        with pytest.raises(ConceptAgentError):
            await diversify(briefs, mock)

    async def test_passes_schema_to_provider(self):
        briefs = make_test_briefs(2)
        response = {
            "keep": [0, 1],
            "mutate": [],
            "drop": [],
        }
        mock = MockLLMProvider(response=response)

        await diversify(briefs, mock)

        assert mock.calls[0]["schema"] is not None
