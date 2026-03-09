"""Shared test helpers for concept agent tests."""

from uuid import uuid4

from app.schemas.brief import BriefCreate
from app.schemas.project import GameProfileRead


def make_game_profile(**overrides) -> GameProfileRead:
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


def make_expand_response(**overrides) -> dict:
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


def make_test_briefs(count: int = 3) -> list[BriefCreate]:
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
