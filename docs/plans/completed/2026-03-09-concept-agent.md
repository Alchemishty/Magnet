# Concept Agent Implementation Plan

**Goal:** Implement the three-step Concept Agent pipeline (STRATEGIZE, EXPAND, DIVERSIFY) that generates diverse creative briefs from a GameProfile using the LLMProvider protocol.

**Architecture:** The agent is composed of three independent async functions — `strategize`, `expand`, and `diversify` — each taking structured input and returning structured output via JSON-mode LLM calls. A `ConceptAgent` orchestrator class chains them, accepting a `GameProfileRead` schema and an `LLMProvider`, returning a list of `BriefCreate` schemas. System prompts live in a dedicated module with the hook taxonomy embedded as a constant.

## Assumptions

- The LLMProvider protocol in `providers/base.py` is stable and sufficient (messages + optional JSON schema).
- All LLM responses use JSON mode — the `schema` parameter is always provided.
- The agent operates on Pydantic schemas (`GameProfileRead`, `BriefCreate`), not ORM models directly.
- The agent does not persist briefs — the caller (service or route layer) handles persistence.
- Each pipeline step is a pure async function that can be tested in isolation with MockLLMProvider.
- Scene plans follow the structure defined in the design doc (scenes list with strategy/type/duration/params, plus audio section).
- The hook taxonomy is a static constant for now; extensibility via DB/config is deferred.

## Open Questions

- None currently. The design doc and domain glossary provide sufficient specification.

## Context and Orientation

- **Files to read before starting:**
  - `docs/architecture.md` — layer rules, agent dependency boundaries
  - `docs/conventions.md` — naming, imports, error handling, provider pattern
  - `docs/domain.md` — hook taxonomy, CreativeBrief definition, Concept Agent steps
  - `docs/testing.md` — test file location, mock pattern, factory pattern
  - `packages/api/app/providers/base.py` — LLMProvider protocol
  - `packages/api/app/schemas/brief.py` — BriefCreate schema
  - `packages/api/app/schemas/project.py` — GameProfileRead schema
  - `packages/api/tests/helpers/factories.py` — existing factory functions
  - `docs/plans/active/2026-03-09-agentic-ua-creative-platform-design.md` — section 4 (Concept Agent pipeline, hook taxonomy, prompt architecture)
- **Patterns to follow:** Provider abstraction pattern and import ordering from `docs/conventions.md`
- **Related decisions:** None yet — this is the first agent implementation.
- **Similar existing code:** `packages/api/app/providers/base.py` (Protocol pattern), `packages/api/tests/helpers/factories.py` (test data builders)

## Steps

### Step 1: System Prompts Module ✅

**Files:** `packages/api/app/agents/prompts.py`
**Tests:** `packages/api/tests/unit/agents/test_prompts.py`
**What to do:**

Create `packages/api/app/agents/prompts.py` containing:

1. `HOOK_TAXONOMY` — a list of dicts, each with `category`, `examples`, and `best_for` fields, matching the 8 hook categories from the domain glossary (Fail/Challenge, Satisfaction, Comparison, Emotional, UGC-style, Fake gameplay, FOMO/Social, Tutorial bait).
2. `STRATEGIZE_SYSTEM_PROMPT` — a string constant. Instructs the LLM to analyze a game profile and return creative directions. Must embed the hook taxonomy. Output schema: `{"directions": [{"hook_type": str, "emotion": str, "angle": str}]}`.
3. `EXPAND_SYSTEM_PROMPT` — a string constant. Instructs the LLM to take a creative direction and game profile, return a full brief with scene plan. Output schema should match `BriefCreate` fields plus a `scene_plan` dict with `scenes` list and `audio` section (each scene tagged COMPOSE/GENERATE/RENDER).
4. `DIVERSIFY_SYSTEM_PROMPT` — a string constant. Instructs the LLM to review a list of briefs for redundancy, score diversity, and suggest mutations. Output schema: `{"keep": [int], "mutate": [{"index": int, "mutation": str}], "drop": [int]}`.
5. Helper functions `build_strategize_messages(game_profile: dict) -> list[dict]`, `build_expand_messages(game_profile: dict, direction: dict) -> list[dict]`, `build_diversify_messages(briefs: list[dict]) -> list[dict]` that construct the full message lists (system + user) for each step.
6. JSON schema constants `STRATEGIZE_SCHEMA`, `EXPAND_SCHEMA`, `DIVERSIFY_SCHEMA` — the `schema` dicts passed to `LLMProvider.generate()`.

Tests: verify that each `build_*` function returns a list of dicts with `role` and `content` keys, that the system message contains the expected prompt, and that user messages contain the serialized input data. Verify `HOOK_TAXONOMY` has exactly 8 entries.

**Verify:** `cd packages/api && pytest tests/unit/agents/test_prompts.py -x`

---

### Step 2: MockLLMProvider ✅

**Files:** `packages/api/tests/helpers/mocks.py`
**Tests:** `packages/api/tests/unit/helpers/test_mocks.py`
**What to do:**

Create `packages/api/tests/helpers/mocks.py` containing:

1. `MockLLMProvider` — a class that satisfies the `LLMProvider` protocol. Constructor accepts either a single `response: dict` (returned on every call) or `responses: list[dict]` (returned in sequence, cycling if exhausted). Stores all calls in a `self.calls: list[dict]` attribute (each entry has `messages` and `schema` keys). The `async def generate(self, messages: list[dict], schema: dict | None = None) -> dict` method appends to `self.calls` and returns the appropriate response.
2. `MockLLMProviderError` — a variant that raises a specified exception on `generate()`, for testing error paths.

Tests: verify MockLLMProvider records calls, returns single response, returns sequential responses, and that MockLLMProviderError raises on call.

**Verify:** `cd packages/api && pytest tests/unit/helpers/test_mocks.py -x`

---

### Step 3: STRATEGIZE Step ✅

**Files:** `packages/api/app/agents/concept_agent.py`
**Tests:** `packages/api/tests/unit/agents/test_concept_agent.py`
**What to do:**

Create `packages/api/app/agents/concept_agent.py` with an async function:

```python
async def strategize(
    game_profile: GameProfileRead,
    llm: LLMProvider,
) -> list[dict]:
```

This function:
1. Calls `build_strategize_messages()` with the game profile serialized to dict.
2. Calls `llm.generate(messages, schema=STRATEGIZE_SCHEMA)`.
3. Parses the response, extracts the `directions` list.
4. Validates each direction has `hook_type`, `emotion`, and `angle` keys.
5. Returns the list of direction dicts.
6. Raises a typed `ConceptAgentError` (defined in the same module) if the LLM response is malformed.

Tests: use `MockLLMProvider` with a canned strategize response. Verify correct messages are passed to the provider. Verify output is a list of direction dicts. Test malformed response raises `ConceptAgentError`. Use `create_test_game_profile` factory for input (convert to `GameProfileRead` via `GameProfileRead.model_validate()`).

**Verify:** `cd packages/api && pytest tests/unit/agents/test_concept_agent.py::TestStrategize -x`

---

### Step 4: EXPAND Step ✅

**Files:** `packages/api/app/agents/concept_agent.py`
**Tests:** `packages/api/tests/unit/agents/test_concept_agent.py`
**What to do:**

Add an async function to `concept_agent.py`:

```python
async def expand(
    game_profile: GameProfileRead,
    directions: list[dict],
    llm: LLMProvider,
) -> list[BriefCreate]:
```

This function:
1. Iterates over each direction in `directions`.
2. For each direction, calls `build_expand_messages()` with the game profile dict and direction dict.
3. Calls `llm.generate(messages, schema=EXPAND_SCHEMA)`.
4. Parses the response into a `BriefCreate` schema, mapping LLM output fields to schema fields. Sets `generated_by="agent"`, `status="draft"`. The `scene_plan` field holds the full scene plan dict from the LLM response.
5. Collects all `BriefCreate` instances into a list and returns it.
6. Raises `ConceptAgentError` if any LLM response cannot be parsed into a valid `BriefCreate`.

Tests: use `MockLLMProvider` with `responses` list (one per direction). Verify each call gets the correct direction in its messages. Verify output is a list of `BriefCreate` with correct fields populated. Verify `scene_plan` contains `scenes` with strategy tags. Test with 1 direction and with 3 directions.

**Verify:** `cd packages/api && pytest tests/unit/agents/test_concept_agent.py::TestExpand -x`

---

### Step 5: DIVERSIFY Step ✅

**Files:** `packages/api/app/agents/concept_agent.py`
**Tests:** `packages/api/tests/unit/agents/test_concept_agent.py`
**What to do:**

Add an async function to `concept_agent.py`:

```python
async def diversify(
    briefs: list[BriefCreate],
    llm: LLMProvider,
) -> list[BriefCreate]:
```

This function:
1. Serializes the briefs list to dicts and calls `build_diversify_messages()`.
2. Calls `llm.generate(messages, schema=DIVERSIFY_SCHEMA)`.
3. Parses the response which contains `keep` (indices to keep as-is), `mutate` (indices with mutation descriptions), and `drop` (indices to remove).
4. Builds the final list: keeps briefs at `keep` indices unchanged, applies mutations to briefs at `mutate` indices by updating the `narrative_angle` or `hook_type` fields based on the mutation description (simple field override for MVP), and drops briefs at `drop` indices.
5. Returns the filtered/mutated list of `BriefCreate`.
6. Raises `ConceptAgentError` if response is malformed or indices are out of range.

Tests: use `MockLLMProvider` with a diversify response that keeps some, mutates some, drops some. Verify the output list length matches `len(keep) + len(mutate)`. Verify mutated briefs have updated fields. Verify dropped briefs are absent. Test edge case: all kept (no mutations, no drops). Test out-of-range index raises `ConceptAgentError`.

**Verify:** `cd packages/api && pytest tests/unit/agents/test_concept_agent.py::TestDiversify -x`

---

### Step 6: ConceptAgent Orchestrator ✅

**Files:** `packages/api/app/agents/concept_agent.py`, `packages/api/app/agents/__init__.py`
**Tests:** `packages/api/tests/unit/agents/test_concept_agent.py`
**What to do:**

Add a class to `concept_agent.py`:

```python
class ConceptAgent:
    def __init__(self, llm: LLMProvider):
        self.llm = llm

    async def generate_briefs(
        self, game_profile: GameProfileRead
    ) -> list[BriefCreate]:
```

The `generate_briefs` method:
1. Calls `strategize(game_profile, self.llm)` to get directions.
2. Calls `expand(game_profile, directions, self.llm)` to get full briefs.
3. Calls `diversify(briefs, self.llm)` to get the final diverse set.
4. Returns the final list of `BriefCreate` schemas.
5. Lets `ConceptAgentError` propagate from any step (no swallowing).

Update `packages/api/app/agents/__init__.py` to export `ConceptAgent` and `ConceptAgentError`.

Tests: use `MockLLMProvider` with `responses` list containing responses for all three steps (strategize response, then N expand responses, then diversify response). Verify the full chain runs end-to-end. Verify `llm.calls` has the expected number of calls (1 + N + 1 where N is the number of directions). Verify the final output is a list of `BriefCreate`. Test that an error in the strategize step prevents expand/diversify from running.

**Verify:** `cd packages/api && pytest tests/unit/agents/test_concept_agent.py::TestConceptAgent -x`

---

## Validation

Run these commands in order to verify the complete implementation:

```bash
cd packages/api && ruff check .
cd packages/api && ruff format --check .
cd packages/api && pytest tests/unit/agents/ -x
cd packages/api && pytest tests/unit/helpers/test_mocks.py -x
cd packages/api && pytest tests/unit/ -x
bash enforcement/run-all.sh
```

## Decision Log

(empty)
