# LLM Provider Implementation Plan

**Goal:** Create concrete Claude and OpenAI implementations of the `LLMProvider` Protocol so the ConceptAgent can make real LLM calls, and wire the active provider into the concept generation route.
**Architecture:** New provider modules live in `providers/llm/` (repository-adjacent, cross-cutting layer). Each uses `httpx.AsyncClient` for async HTTP. A provider factory in `providers/llm/__init__.py` selects the active provider from an env var. The route layer injects the provider into the ConceptAgent via FastAPI `Depends`. An `ExternalProviderError` error type surfaces API failures cleanly.

## Assumptions
- `httpx>=0.27` is already in `pyproject.toml` dependencies (confirmed)
- `pytest-asyncio>=0.23` is available with `asyncio_mode = "auto"` (confirmed)
- No SDK packages needed — both Claude and OpenAI APIs are called via raw `httpx` to keep dependencies minimal and the abstraction honest
- API keys come from environment variables: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`
- The `schema` parameter maps to Claude's tool-use JSON mode and OpenAI's `response_format` / function calling for structured output

## Open Questions
- None — the Protocol, ConceptAgent, and route stub are all in place. This plan fills the gap.

## Context and Orientation
- **Files to read before starting:** `app/providers/base.py`, `app/agents/concept_agent.py`, `app/services/concept_service.py`, `app/routes/briefs.py`, `app/routes/dependencies.py`, `app/errors.py`
- **Patterns to follow:** Provider abstraction pattern from `docs/conventions.md`; error handling pattern (typed errors in services/providers, HTTPException only in routes); dependency injection via `dependencies.py`
- **Similar existing code:** `MockLLMProvider` in `tests/helpers/mocks.py` — shows the interface contract

## Steps

### Step 1: [DONE] Add ExternalProviderError
**Files:** `packages/api/app/errors.py`
**Tests:** `packages/api/tests/unit/test_errors.py`
**What to do:** Add `ExternalProviderError` to the errors module. It should accept `provider_name: str` and `message: str`, storing both as attributes. This is the typed error that provider implementations raise when an external API call fails. Follow the existing pattern of `DatabaseError` and `NotFoundError`.
**Verify:** `cd packages/api && pytest tests/unit/test_errors.py -x`

### Step 2: [DONE] Claude provider
**Files:** `packages/api/app/providers/llm/__init__.py`, `packages/api/app/providers/llm/claude.py`
**Tests:** `packages/api/tests/unit/providers/__init__.py`, `packages/api/tests/unit/providers/test_claude.py`
**What to do:** Create `ClaudeProvider` class implementing the `LLMProvider` protocol.
- Constructor takes `api_key: str` and optional `model: str` (default `"claude-sonnet-4-20250514"`).
- Creates an `httpx.AsyncClient` with base URL `https://api.anthropic.com`, `x-api-key` header, `anthropic-version: 2023-06-01` header, and `content-type: application/json`.
- `generate()` method:
  - Converts the `messages` list to Anthropic format (extract system message separately, keep user/assistant messages).
  - If `schema` is provided, use tool-use to force structured JSON: add a single tool definition with the schema as `input_schema`, set `tool_choice={"type": "tool", "name": "structured_output"}`. Parse the tool call result from the response.
  - If `schema` is None, parse `content[0].text` as JSON.
  - Raise `ExternalProviderError("claude", ...)` on HTTP errors (non-2xx), JSON parse failures, or unexpected response shapes.
  - Return the parsed dict.
- `__init__.py` is empty for now (factory comes in step 4).
**Verify:** `cd packages/api && pytest tests/unit/providers/test_claude.py -x`

### Step 3: [DONE] OpenAI provider
**Files:** `packages/api/app/providers/llm/openai.py`
**Tests:** `packages/api/tests/unit/providers/test_openai.py`
**What to do:** Create `OpenAIProvider` class implementing the `LLMProvider` protocol.
- Constructor takes `api_key: str` and optional `model: str` (default `"gpt-4o"`).
- Creates an `httpx.AsyncClient` with base URL `https://api.openai.com/v1`, `Authorization: Bearer {api_key}` header, `content-type: application/json`.
- `generate()` method:
  - Passes `messages` directly (OpenAI format matches the protocol's message format).
  - If `schema` is provided, use `response_format={"type": "json_schema", "json_schema": {"name": "response", "strict": True, "schema": schema}}`.
  - If `schema` is None, use `response_format={"type": "json_object"}` and append a system instruction asking for JSON.
  - Parse `choices[0].message.content` as JSON.
  - Raise `ExternalProviderError("openai", ...)` on HTTP errors, JSON parse failures, or unexpected response shapes.
  - Return the parsed dict.
**Verify:** `cd packages/api && pytest tests/unit/providers/test_openai.py -x`

### Step 4: [DONE] Provider factory
**Files:** `packages/api/app/providers/llm/__init__.py`
**Tests:** `packages/api/tests/unit/providers/test_llm_factory.py`
**What to do:** Create a `get_llm_provider()` factory function that reads `LLM_PROVIDER` env var (default `"claude"`) and the corresponding API key env var, then returns the appropriate provider instance.
- `"claude"` → reads `ANTHROPIC_API_KEY`, returns `ClaudeProvider(api_key=...)`
- `"openai"` → reads `OPENAI_API_KEY`, returns `OpenAIProvider(api_key=...)`
- Raises `ValueError` if `LLM_PROVIDER` is unrecognized.
- Raises `ValueError` if the required API key env var is missing.
- Optional `LLM_MODEL` env var overrides the default model for whichever provider is selected.
**Verify:** `cd packages/api && pytest tests/unit/providers/test_llm_factory.py -x`

### Step 5: [DONE] Wire provider into concept generation route
**Files:** `packages/api/app/routes/dependencies.py`, `packages/api/app/routes/briefs.py`
**Tests:** `packages/api/tests/unit/routes/test_briefs.py`
**What to do:**
- In `dependencies.py`: add a `get_llm_provider()` dependency that calls the factory from step 4. Add a `get_concept_agent()` dependency that takes the LLM provider via `Depends(get_llm_provider)` and returns a `ConceptAgent(llm=provider)`.
- In `briefs.py`: replace the 501 stub `generate_concepts` route with a real implementation:
  - Inject `ConceptService` and `ConceptAgent` via `Depends`.
  - Call `service.generate_concepts(project_id, agent.generate_briefs)`.
  - Return the list of `BriefRead` schemas.
  - Catch `NotFoundError` → 404, `ValidationError` → 422, `ExternalProviderError` → 502, `ConceptAgentError` → 502.
**Verify:** `cd packages/api && pytest tests/unit/routes/ -x`

## Validation
- Run full test suite: `cd packages/api && pytest -x`
- Run linter: `cd packages/api && ruff check .`
- Run enforcement: `bash enforcement/run-all.sh`
- Expected: all tests pass, no lint errors, no enforcement violations. The `generate_concepts` route returns 200 with briefs (in tests with mocked httpx), and the 501 stub is gone.

## Decision Log
