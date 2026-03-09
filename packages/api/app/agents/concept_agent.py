"""Concept Agent: STRATEGIZE -> EXPAND -> DIVERSIFY pipeline."""

from app.agents.prompts import (
    STRATEGIZE_SCHEMA,
    build_strategize_messages,
)
from app.providers.base import LLMProvider
from app.schemas.project import GameProfileRead


class ConceptAgentError(Exception):
    """Raised when the Concept Agent encounters a malformed LLM response."""


_DIRECTION_REQUIRED_KEYS = {"hook_type", "emotion", "angle"}


async def strategize(
    game_profile: GameProfileRead,
    llm: LLMProvider,
) -> list[dict]:
    """Analyze a game profile and generate creative directions.

    Returns a list of direction dicts, each with hook_type, emotion, angle.
    """
    profile_dict = game_profile.model_dump(mode="json")
    messages = build_strategize_messages(profile_dict)
    response = await llm.generate(messages, schema=STRATEGIZE_SCHEMA)

    if "directions" not in response:
        raise ConceptAgentError(
            "LLM response missing 'directions' key"
        )

    directions = response["directions"]
    if not isinstance(directions, list):
        raise ConceptAgentError(
            "LLM response 'directions' is not a list"
        )

    for i, d in enumerate(directions):
        missing = _DIRECTION_REQUIRED_KEYS - set(d.keys())
        if missing:
            raise ConceptAgentError(
                f"Direction {i} missing keys: {missing}"
            )

    return directions
