"""Concept Agent: STRATEGIZE -> EXPAND -> DIVERSIFY pipeline."""

from pydantic import ValidationError

from app.agents.prompts import (
    DIVERSIFY_SCHEMA,
    EXPAND_SCHEMA,
    STRATEGIZE_SCHEMA,
    build_diversify_messages,
    build_expand_messages,
    build_strategize_messages,
)
from app.providers.base import LLMProvider
from app.schemas.brief import BriefCreate
from app.schemas.project import GameProfileRead


class ConceptAgentError(Exception):
    """Raised when the Concept Agent encounters a malformed LLM response."""


_DIRECTION_REQUIRED_KEYS = {"hook_type", "emotion", "angle"}
_SCENE_REQUIRED_KEYS = {"strategy", "type", "duration"}


def _ensure_dict(response: object, step: str) -> dict:
    if not isinstance(response, dict):
        raise ConceptAgentError(
            f"{step} response is not a dict: {type(response).__name__}"
        )
    return response
_EXPAND_REQUIRED_FIELDS = {
    "hook_type",
    "narrative_angle",
    "script",
    "target_emotion",
}
_VALID_SCENE_STRATEGIES = {"COMPOSE", "GENERATE", "RENDER"}


async def strategize(
    game_profile: GameProfileRead,
    llm: LLMProvider,
) -> list[dict]:
    """Analyze a game profile and generate creative directions.

    Returns a list of direction dicts, each with hook_type, emotion, angle.
    """
    profile_dict = game_profile.model_dump(mode="json")
    messages = build_strategize_messages(profile_dict)
    response = _ensure_dict(
        await llm.generate(messages, schema=STRATEGIZE_SCHEMA),
        "STRATEGIZE",
    )

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
        if not isinstance(d, dict):
            raise ConceptAgentError(
                f"Direction {i} is not a dict"
            )
        missing = _DIRECTION_REQUIRED_KEYS - set(d.keys())
        if missing:
            raise ConceptAgentError(
                f"Direction {i} missing keys: {missing}"
            )
        for key in _DIRECTION_REQUIRED_KEYS:
            if not isinstance(d[key], str) or not d[key].strip():
                raise ConceptAgentError(
                    f"Direction {i} has invalid '{key}': "
                    f"expected non-empty string"
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
        response = _ensure_dict(
            await llm.generate(messages, schema=EXPAND_SCHEMA),
            "EXPAND",
        )

        for field in _EXPAND_REQUIRED_FIELDS:
            if not response.get(field):
                raise ConceptAgentError(
                    f"Expand response missing required field '{field}'"
                )

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

        scenes = brief.scene_plan["scenes"]
        if not isinstance(scenes, list) or len(scenes) == 0:
            raise ConceptAgentError(
                "scene_plan must have at least one scene"
            )

        for j, scene in enumerate(scenes):
            if not isinstance(scene, dict):
                raise ConceptAgentError(
                    f"Scene {j} is not a dict"
                )
            missing = _SCENE_REQUIRED_KEYS - set(scene.keys())
            if missing:
                raise ConceptAgentError(
                    f"Scene {j} missing keys: {missing}"
                )
            if scene["strategy"] not in _VALID_SCENE_STRATEGIES:
                raise ConceptAgentError(
                    f"Scene {j} has invalid strategy "
                    f"'{scene['strategy']}', "
                    f"expected one of {_VALID_SCENE_STRATEGIES}"
                )

        briefs.append(brief)

    return briefs


_MUTABLE_FIELDS = {"hook_type", "narrative_angle"}


async def diversify(
    briefs: list[BriefCreate],
    llm: LLMProvider,
) -> list[BriefCreate]:
    """Review briefs for redundancy and apply diversity mutations.

    Returns a filtered/mutated list of BriefCreate schemas.
    """
    briefs_dicts = [b.model_dump(mode="json") for b in briefs]
    messages = build_diversify_messages(briefs_dicts)
    response = _ensure_dict(
        await llm.generate(messages, schema=DIVERSIFY_SCHEMA),
        "DIVERSIFY",
    )

    for key in ("keep", "mutate", "drop"):
        if key not in response:
            raise ConceptAgentError(
                f"Diversify response missing '{key}' key"
            )

    keep_indices = response["keep"]
    mutate_entries = response["mutate"]
    drop_indices = response["drop"]

    if not isinstance(keep_indices, list):
        raise ConceptAgentError("'keep' must be a list")
    if not isinstance(mutate_entries, list):
        raise ConceptAgentError("'mutate' must be a list")
    if not isinstance(drop_indices, list):
        raise ConceptAgentError("'drop' must be a list")

    for i, m in enumerate(mutate_entries):
        if not isinstance(m, dict) or "index" not in m:
            raise ConceptAgentError(
                f"mutate entry {i} must be a dict with 'index'"
            )

    num_briefs = len(briefs)

    all_indices = (
        list(keep_indices)
        + [m["index"] for m in mutate_entries]
        + list(drop_indices)
    )
    for idx in all_indices:
        if idx < 0 or idx >= num_briefs:
            raise ConceptAgentError(
                f"Index {idx} out of range for {num_briefs} briefs"
            )

    # Validate disjoint partition
    keep_set = set(keep_indices)
    mutate_set = {m["index"] for m in mutate_entries}
    drop_set = set(drop_indices)
    overlap = (
        (keep_set & mutate_set)
        | (keep_set & drop_set)
        | (mutate_set & drop_set)
    )
    if overlap:
        raise ConceptAgentError(
            f"Indices {overlap} appear in multiple buckets"
        )

    result: list[BriefCreate] = []

    # Add kept briefs
    for idx in keep_indices:
        result.append(briefs[idx])

    # Add mutated briefs
    for entry in mutate_entries:
        idx = entry["index"]
        mutation = entry.get("mutation", "")
        if not isinstance(mutation, str) or ":" not in mutation:
            raise ConceptAgentError(
                f"Mutation for brief {idx} must use "
                f"'field:value' format, got: '{mutation}'"
            )

        field, value = mutation.split(":", 1)
        field = field.strip()
        value = value.strip()
        if field not in _MUTABLE_FIELDS or not value:
            raise ConceptAgentError(
                f"Mutation for brief {idx} targets invalid "
                f"field '{field}' or empty value. "
                f"Allowed fields: {_MUTABLE_FIELDS}"
            )

        brief = briefs[idx].model_copy(update={field: value})
        result.append(brief)

    return result


class ConceptAgent:
    """Orchestrates the STRATEGIZE -> EXPAND -> DIVERSIFY pipeline.

    Accepts a GameProfileRead and an LLMProvider, returns a list of
    BriefCreate schemas ready for persistence.
    """

    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def generate_briefs(
        self, game_profile: GameProfileRead
    ) -> list[BriefCreate]:
        """Run the full concept generation pipeline."""
        directions = await strategize(game_profile, self.llm)
        briefs = await expand(
            game_profile, directions, self.llm
        )
        return await diversify(briefs, self.llm)
