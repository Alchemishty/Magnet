# Patterns

## Provider lifecycle: always implement aclose()

LLM providers (and future TTS/music/image/video providers) create `httpx.AsyncClient` instances. These must be closed after use. Every provider should implement `aclose()` and the FastAPI dependency should be an async generator with `try/finally` cleanup.

- **Context:** Any provider that holds an httpx client or similar resource
- **Source:** CodeRabbit review on PR #6 (2026-03-10 LLM provider feature)

## AsyncMock for async service methods in route tests

When mocking services that have `async` methods (like `ConceptService.generate_concepts`), use `AsyncMock()` not `MagicMock()`. `MagicMock` return values aren't awaitable, causing `TypeError: object can't be used in 'await' expression`.

- **Context:** Route tests that call async service methods via `TestClient`
- **Source:** 2026-03-10 LLM provider feature, step 5

## Catch ValueError from factory/config in routes

Provider factories raise `ValueError` for missing env vars or unknown provider names. Routes that depend on providers should catch `ValueError` and return a structured HTTP error (500 with config error message), not let it bubble as an unhandled 500.

- **Context:** Any route that injects a provider via `Depends`
- **Source:** CodeRabbit review on PR #6 (2026-03-10 LLM provider feature)

## Claude API: tool-use for structured JSON output

To get structured JSON from Claude, use a single tool definition with the desired schema as `input_schema` and `tool_choice={"type": "tool", "name": "..."}`. Parse `content[0].input` from the response. For OpenAI, use `response_format={"type": "json_schema", ...}` and parse `choices[0].message.content`.

- **Context:** Any code that needs structured JSON from LLM providers
- **Source:** 2026-03-10 LLM provider feature

## Commit before dispatching async tasks

`BaseRepository.create()` calls `session.flush()`, not `session.commit()`. The `get_db()` dependency calls `session.close()` on cleanup which rolls back unflushed changes. When dispatching a Celery task that needs to read a just-created row, explicitly `session.commit()` before calling `dispatch_task()`, otherwise the worker won't find the row.

- **Context:** Any service method that creates a DB record then dispatches an async task
- **Source:** CodeRabbit review on PR #7 (2026-03-10 Celery task integration)

## Use distinct React Query keys for list vs detail queries

`useQuery({ queryKey: ["projects", userId] })` for a list and `useQuery({ queryKey: ["projects", id] })` for a detail will share the same cache entry if userId happens to equal id. Use `["projects", "list", userId]` and `["projects", "detail", id]` to namespace them. CodeRabbit catches this.

- **Context:** Any React Query hooks where list and detail queries share a key prefix
- **Source:** CodeRabbit review on PR #13 (2026-03-11 frontend dashboard)

## Handle query errors explicitly in forms that auto-create on missing data

If a form component uses a query to check for existing data (e.g., `useGameProfile`) and falls through to "create" mode when data is `undefined`, a transient query failure looks like "no data exists" and triggers a create. Always check `isError` separately and show an error state rather than falling through to create mode.

- **Context:** Any form that distinguishes "create" vs "update" based on query results
- **Source:** CodeRabbit review on PR #13 (2026-03-11 frontend dashboard)

## Inject Celery tasks via callables, not direct imports

Services should accept task dispatch as an optional `Callable[[str], object]` parameter rather than importing Celery tasks directly. This keeps the service testable (mock the callable) and respects import direction (services don't depend on tasks). The route layer injects the actual `.delay` via a FastAPI `Depends` function.

- **Context:** Any service that needs to dispatch a Celery task
- **Source:** 2026-03-10 Celery task integration feature
