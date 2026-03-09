"""Concept Agent: STRATEGIZE -> EXPAND -> DIVERSIFY pipeline."""

from pydantic import ValidationError

from app.agents.prompts import (
    EXPAND_SCHEMA,
    STRATEGIZE_SCHEMA,
    build_expand_messages,
    build_strategize_messages,
)
from app.providers.base import LLMProvider
from app.schemas.brief import BriefCreate
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


async def expand(
    game_profile: GameProfileRead,
    directions: list[dict],
    llm: LLMProvider,
) -> list[BriefCreate]:
    """Expand creative directions into full creative briefs.

    Returns a list of BriefCreate schemas, one per direction.
    """
    profile_dict = game_profile.model_dump(mode="json")
    briefs: list[BriefCreate] = []

    for direction in directions:
        messages = build_expand_messages(profile_dict, direction)
        response = await llm.generate(messages, schema=EXPAND_SCHEMA)

        try:
            brief = BriefCreate(
                project_id=game_profile.project_id,
                hook_type=response.get("hook_type"),
                narrative_angle=response.get("narrative_angle"),
                script=response.get("script"),
                voiceover_text=response.get("voiceover_text"),
                target_emotion=response.get("target_emotion"),
                cta_text=response.get("cta_text"),
                target_format=response.get(
                    "target_format", "9:16"
                ),
                target_duration=response.get(
                    "target_duration", 15
                ),
                scene_plan=response.get("scene_plan"),
                status="draft",
                generated_by="agent",
            )
        except (ValidationError, KeyError, TypeError) as e:
            raise ConceptAgentError(
                f"Failed to parse expand response: {e}"
            ) from e

        if brief.scene_plan is None or "scenes" not in brief.scene_plan:
            raise ConceptAgentError(
                "Expand response missing scene_plan with scenes"
            )

        briefs.append(brief)

    return briefs
