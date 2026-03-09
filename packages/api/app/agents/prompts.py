"""System prompts, message builders, and JSON schemas for the Concept Agent."""

import json

HOOK_TAXONOMY: list[dict] = [
    {
        "category": "Fail/Challenge",
        "examples": '"I can\'t get past level 5", "99% fail"',
        "best_for": "Casual, puzzle",
    },
    {
        "category": "Satisfaction",
        "examples": "Oddly satisfying loops, ASMR-style",
        "best_for": "Idle, merge, casual",
    },
    {
        "category": "Comparison",
        "examples": '"Level 1 vs Level 100", "Noob vs Pro"',
        "best_for": "RPG, strategy",
    },
    {
        "category": "Emotional",
        "examples": "Story-driven narrative, character journey",
        "best_for": "RPG, narrative",
    },
    {
        "category": "UGC-style",
        "examples": 'Fake reaction, "I found this game and..."',
        "best_for": "All genres",
    },
    {
        "category": "Fake gameplay",
        "examples": "Pin-pull, choice-based, exaggerated",
        "best_for": "Casual, hyper-casual",
    },
    {
        "category": "FOMO/Social",
        "examples": '"Everyone\'s playing this", trending',
        "best_for": "All genres",
    },
    {
        "category": "Tutorial bait",
        "examples": '"Here\'s a trick most players don\'t know"',
        "best_for": "Strategy, mid-core",
    },
]

_TAXONOMY_TEXT = "\n".join(
    f"- {h['category']}: {h['examples']} (best for: {h['best_for']})"
    for h in HOOK_TAXONOMY
)

STRATEGIZE_SYSTEM_PROMPT = f"""You are a mobile game UA creative strategist. \
Analyze the provided game profile and generate diverse creative directions \
for video ad concepts.

Use the following hook taxonomy to guide your choices:
{_TAXONOMY_TEXT}

For each direction, specify:
- hook_type: one of the hook categories above
- emotion: the target emotion to evoke in the viewer
- angle: a short description of the creative angle

Return your response as JSON matching the provided schema."""

EXPAND_SYSTEM_PROMPT = """You are a mobile game UA creative director. \
Given a game profile and a creative direction, produce a full creative brief \
with a detailed scene-by-scene plan.

Each scene in the scene plan must be tagged with one of three strategies:
- COMPOSE: use real uploaded assets (gameplay footage, screenshots, logos)
- GENERATE: AI-create elements (voiceovers via TTS, music, AI avatars, imagery)
- RENDER: programmatically code-render (animated text, UI mockups, progress bars)

The scene plan should include a list of scenes and an audio section. \
Each scene has: strategy (COMPOSE/GENERATE/RENDER), type, duration, and params.

Return your response as JSON matching the provided schema."""

DIVERSIFY_SYSTEM_PROMPT = """You are a creative diversity reviewer for mobile game \
UA ad concepts. Review the provided list of creative briefs for redundancy and \
suggest how to maximize diversity.

For each brief, decide whether to:
- keep: retain the brief as-is (add its index to the "keep" list)
- mutate: modify the brief to increase diversity (add its index and a mutation \
description to the "mutate" list, e.g. change hook_type or narrative_angle)
- drop: remove the brief as redundant (add its index to the "drop" list)

Return your response as JSON matching the provided schema."""

STRATEGIZE_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "directions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "hook_type": {"type": "string"},
                    "emotion": {"type": "string"},
                    "angle": {"type": "string"},
                },
                "required": ["hook_type", "emotion", "angle"],
            },
        },
    },
    "required": ["directions"],
}

EXPAND_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "hook_type": {"type": "string"},
        "narrative_angle": {"type": "string"},
        "script": {"type": "string"},
        "voiceover_text": {"type": "string"},
        "target_emotion": {"type": "string"},
        "cta_text": {"type": "string"},
        "target_format": {"type": "string"},
        "target_duration": {"type": "integer"},
        "scene_plan": {
            "type": "object",
            "properties": {
                "scenes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "strategy": {"type": "string"},
                            "type": {"type": "string"},
                            "duration": {"type": "number"},
                            "params": {"type": "object"},
                        },
                        "required": ["strategy", "type", "duration"],
                    },
                },
                "audio": {"type": "object"},
            },
            "required": ["scenes"],
        },
    },
    "required": [
        "hook_type",
        "narrative_angle",
        "script",
        "target_emotion",
        "scene_plan",
    ],
}

DIVERSIFY_SCHEMA: dict = {
    "type": "object",
    "properties": {
        "keep": {
            "type": "array",
            "items": {"type": "integer"},
        },
        "mutate": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "index": {"type": "integer"},
                    "mutation": {"type": "string"},
                },
                "required": ["index", "mutation"],
            },
        },
        "drop": {
            "type": "array",
            "items": {"type": "integer"},
        },
    },
    "required": ["keep", "mutate", "drop"],
}


def build_strategize_messages(game_profile: dict) -> list[dict]:
    """Build message list for the STRATEGIZE step."""
    return [
        {"role": "system", "content": STRATEGIZE_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Analyze this game profile and generate creative directions:\n\n"
                + json.dumps(game_profile, indent=2, default=str)
            ),
        },
    ]


def build_expand_messages(game_profile: dict, direction: dict) -> list[dict]:
    """Build message list for the EXPAND step."""
    return [
        {"role": "system", "content": EXPAND_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Game profile:\n"
                + json.dumps(game_profile, indent=2, default=str)
                + "\n\nCreative direction:\n"
                + json.dumps(direction, indent=2, default=str)
            ),
        },
    ]


def build_diversify_messages(briefs: list[dict]) -> list[dict]:
    """Build message list for the DIVERSIFY step."""
    return [
        {"role": "system", "content": DIVERSIFY_SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                "Review these creative briefs for diversity:\n\n"
                + json.dumps(briefs, indent=2, default=str)
            ),
        },
    ]
