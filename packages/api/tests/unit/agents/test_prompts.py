"""Tests for the Concept Agent prompts module."""

from app.agents.prompts import (
    DIVERSIFY_SCHEMA,
    DIVERSIFY_SYSTEM_PROMPT,
    EXPAND_SCHEMA,
    EXPAND_SYSTEM_PROMPT,
    HOOK_TAXONOMY,
    STRATEGIZE_SCHEMA,
    STRATEGIZE_SYSTEM_PROMPT,
    build_diversify_messages,
    build_expand_messages,
    build_strategize_messages,
)


class TestHookTaxonomy:
    def test_has_eight_categories(self):
        assert len(HOOK_TAXONOMY) == 8

    def test_each_entry_has_required_fields(self):
        for entry in HOOK_TAXONOMY:
            assert "category" in entry
            assert "examples" in entry
            assert "best_for" in entry

    def test_expected_categories_present(self):
        categories = {entry["category"] for entry in HOOK_TAXONOMY}
        expected = {
            "Fail/Challenge",
            "Satisfaction",
            "Comparison",
            "Emotional",
            "UGC-style",
            "Fake gameplay",
            "FOMO/Social",
            "Tutorial bait",
        }
        assert categories == expected


class TestSystemPrompts:
    def test_strategize_prompt_contains_hook_taxonomy(self):
        assert "Fail/Challenge" in STRATEGIZE_SYSTEM_PROMPT
        assert "Satisfaction" in STRATEGIZE_SYSTEM_PROMPT
        assert "hook" in STRATEGIZE_SYSTEM_PROMPT.lower()

    def test_expand_prompt_mentions_scene_plan(self):
        assert "scene" in EXPAND_SYSTEM_PROMPT.lower()
        assert "COMPOSE" in EXPAND_SYSTEM_PROMPT
        assert "GENERATE" in EXPAND_SYSTEM_PROMPT
        assert "RENDER" in EXPAND_SYSTEM_PROMPT

    def test_diversify_prompt_mentions_redundancy(self):
        assert "redundan" in DIVERSIFY_SYSTEM_PROMPT.lower()
        prompt_lower = DIVERSIFY_SYSTEM_PROMPT.lower()
        assert "mutation" in prompt_lower or "mutate" in prompt_lower


class TestBuildStrategizeMessages:
    def test_returns_list_of_dicts(self):
        profile = {"genre": "puzzle", "target_audience": "casual"}
        messages = build_strategize_messages(profile)
        assert isinstance(messages, list)
        assert all(isinstance(m, dict) for m in messages)

    def test_has_system_and_user_messages(self):
        profile = {"genre": "puzzle"}
        messages = build_strategize_messages(profile)
        roles = [m["role"] for m in messages]
        assert "system" in roles
        assert "user" in roles

    def test_system_message_contains_prompt(self):
        profile = {"genre": "puzzle"}
        messages = build_strategize_messages(profile)
        system_msg = next(m for m in messages if m["role"] == "system")
        assert STRATEGIZE_SYSTEM_PROMPT in system_msg["content"]

    def test_user_message_contains_profile_data(self):
        profile = {"genre": "puzzle", "target_audience": "casual gamers"}
        messages = build_strategize_messages(profile)
        user_msg = next(m for m in messages if m["role"] == "user")
        assert "puzzle" in user_msg["content"]
        assert "casual gamers" in user_msg["content"]


class TestBuildExpandMessages:
    def test_returns_list_of_dicts(self):
        profile = {"genre": "puzzle"}
        direction = {
            "hook_type": "Fail/Challenge",
            "emotion": "curiosity",
            "angle": "test",
        }
        messages = build_expand_messages(profile, direction)
        assert isinstance(messages, list)
        assert all(isinstance(m, dict) for m in messages)

    def test_has_system_and_user_messages(self):
        profile = {"genre": "puzzle"}
        direction = {
            "hook_type": "Fail/Challenge",
            "emotion": "curiosity",
            "angle": "test",
        }
        messages = build_expand_messages(profile, direction)
        roles = [m["role"] for m in messages]
        assert "system" in roles
        assert "user" in roles

    def test_user_message_contains_direction(self):
        profile = {"genre": "puzzle"}
        direction = {
            "hook_type": "Fail/Challenge",
            "emotion": "curiosity",
            "angle": "test angle",
        }
        messages = build_expand_messages(profile, direction)
        user_msg = next(m for m in messages if m["role"] == "user")
        assert "Fail/Challenge" in user_msg["content"]
        assert "test angle" in user_msg["content"]


class TestBuildDiversifyMessages:
    def test_returns_list_of_dicts(self):
        briefs = [{"hook_type": "Fail/Challenge", "narrative_angle": "test"}]
        messages = build_diversify_messages(briefs)
        assert isinstance(messages, list)
        assert all(isinstance(m, dict) for m in messages)

    def test_has_system_and_user_messages(self):
        briefs = [{"hook_type": "Fail/Challenge"}]
        messages = build_diversify_messages(briefs)
        roles = [m["role"] for m in messages]
        assert "system" in roles
        assert "user" in roles

    def test_user_message_contains_brief_data(self):
        briefs = [{"hook_type": "Fail/Challenge", "narrative_angle": "unique angle"}]
        messages = build_diversify_messages(briefs)
        user_msg = next(m for m in messages if m["role"] == "user")
        assert "unique angle" in user_msg["content"]


class TestSchemas:
    def test_strategize_schema_is_dict(self):
        assert isinstance(STRATEGIZE_SCHEMA, dict)

    def test_expand_schema_is_dict(self):
        assert isinstance(EXPAND_SCHEMA, dict)

    def test_diversify_schema_is_dict(self):
        assert isinstance(DIVERSIFY_SCHEMA, dict)
