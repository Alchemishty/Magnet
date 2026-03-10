# WebSocket Real-Time Progress Implementation Plan

**Goal:** Add WebSocket-based real-time progress updates so the frontend receives live status changes during render job processing, replacing the need for polling.
**Architecture:** Redis pub/sub bridges Celery workers and FastAPI WebSocket connections. Workers publish progress events to `progress:brief:{brief_id}` channels; the WebSocket endpoint at `/ws/briefs/{brief_id}/progress` subscribes per-brief and forwards to connected clients. Progress events are ephemeral (pub/sub) while job status remains the DB source of truth. No new infrastructure — Redis is already deployed for Celery.

## Assumptions
- Redis is available at the URL configured in `CELERY_BROKER_URL` (already required for Celery)
- Progress events are fire-and-forget — if no client is connected, events are lost (DB status is authoritative)
- The Celery worker runs in a separate process and cannot share FastAPI's in-process state
- Auth on the WebSocket endpoint is deferred to a later phase

## Open Questions
(All resolved)
- ~~Subscribe per-job or per-brief?~~ **Per-brief.** A single WebSocket at `/ws/briefs/{brief_id}/progress` subscribes to all jobs for that brief. Workers publish to `progress:brief:{brief_id}` so one subscription covers all jobs.
- ~~Percentage estimates or phase transitions only?~~ **Both.** Include a `progress_pct: int | None` (0-100) field on events. Workers publish percentage estimates at key phases (e.g., PLAN=10, PREPARE=40, ASSEMBLE=70, POST-PROCESS=90, done=100).
- ~~Auth on WebSocket?~~ **Deferred.** No auth for MVP; add in a later phase.

## Context and Orientation
- **Files to read before starting:** `app/worker.py`, `app/tasks/render.py`, `app/routes/jobs.py`, `app/main.py`, `app/db.py`
- **Patterns to follow:** Provider abstraction (docs/conventions/provider-abstraction.md) for the Redis pub/sub client, error handling (docs/conventions/error-handling.md) for WebSocket error paths, session lifecycle (docs/conventions/session-lifecycle.md)
- **Related decisions:** None directly — this is net-new WebSocket infrastructure
- **Similar existing code:** `app/repositories/s3_client.py` follows the factory pattern for infrastructure clients; the Redis pub/sub client should follow the same pattern

## Steps

### Step 1: [DONE] Progress event schemas
**Files:** `packages/api/app/schemas/progress.py`
**Tests:** `packages/api/tests/unit/schemas/test_progress.py`
**What to do:** Create Pydantic models for progress events:
- `ProgressStatus` — a Literal type: `"queued" | "rendering" | "done" | "failed" | "phase_update"`.
- `ProgressEvent` — fields: `job_id: UUID`, `brief_id: UUID`, `status: ProgressStatus`, `phase: str | None` (e.g., "PLAN", "PREPARE", "ASSEMBLE", "POST-PROCESS"), `progress_pct: int | None` (0-100), `message: str | None`, `timestamp: datetime` (defaults to utcnow). Add a `to_channel()` method that returns `f"progress:brief:{self.brief_id}"` and a `to_json()` method using `.model_dump_json()`.
**Verify:** `cd packages/api && pytest tests/unit/schemas/test_progress.py -x`

### Step 2: [DONE] Redis pub/sub client
**Files:** `packages/api/app/repositories/redis_client.py`
**Tests:** `packages/api/tests/unit/repositories/test_redis_client.py`
**What to do:** Create a `RedisClient` class following the same factory pattern as `S3Client`:
- Constructor takes `redis_url: str`.
- `publish(channel: str, message: str) -> None` — publishes a message to a Redis channel using `redis.Redis.publish()`.
- `subscribe(*channels: str)` — returns an async generator that yields messages from one or more channels. Use `redis.asyncio.client.PubSub` for async subscription. Supports subscribing to multiple channels (e.g., multiple job channels) in a single call.
- Factory function `get_redis_client() -> RedisClient` reads `REDIS_URL` env var (falling back to `CELERY_BROKER_URL`, then `redis://localhost:6379/0`). Raises `ValueError` if connection fails.
- Use the `redis` Python package (add to dependencies if not present).
**Verify:** `cd packages/api && pytest tests/unit/repositories/test_redis_client.py -x`

### Step 3: [DONE] Progress publisher service
**Files:** `packages/api/app/services/progress_service.py`
**Tests:** `packages/api/tests/unit/services/test_progress_service.py`
**What to do:** Create `ProgressPublisher` class:
- Constructor takes a `RedisClient` instance.
- `publish(event: ProgressEvent) -> None` — calls `self._redis.publish(event.to_channel(), event.to_json())`.
- This is deliberately thin — it exists so the Celery task can publish progress without knowing Redis details, and so tests can mock it easily.
**Verify:** `cd packages/api && pytest tests/unit/services/test_progress_service.py -x`

### Step 4: [DONE] Integrate progress publishing into render task
**Files:** `packages/api/app/tasks/render.py`
**Tests:** `packages/api/tests/unit/tasks/test_render.py`
**What to do:** Modify `process_render_job` to publish progress events at key lifecycle points. Each event includes `job_id`, `brief_id` (read from the job record), and `progress_pct`:
- After setting status to "rendering": publish `status="rendering", progress_pct=5, message="Render job started"`.
- Phase updates (published by the Video Agent callback — for now, hardcode in task): PLAN=10, PREPARE=40, ASSEMBLE=70, POST-PROCESS=90.
- After completion: publish `status="done", progress_pct=100, message="Render complete"`.
- On failure: publish `status="failed", progress_pct=None, message=str(exc)`.
- Create the `RedisClient` inside the task using the factory function. If Redis is unavailable, log a warning and skip publishing (progress is best-effort). Wrap all publish calls in try/except so a Redis failure never breaks the render pipeline.
- Update existing tests to account for the new publish calls (mock the RedisClient).
**Verify:** `cd packages/api && pytest tests/unit/tasks/test_render.py -x`

### Step 5: [DONE] WebSocket route endpoint
**Files:** `packages/api/app/routes/ws.py`, `packages/api/app/routes/__init__.py`, `packages/api/app/main.py`
**Tests:** `packages/api/tests/unit/routes/test_ws_routes.py`
**What to do:** Create a WebSocket endpoint at `/ws/briefs/{brief_id}/progress`:
- Accept the WebSocket connection.
- Create a `RedisClient` and subscribe to `progress:brief:{brief_id}`.
- Forward each message from the Redis subscription to the WebSocket client as a text frame. Each message contains the `job_id` so the client can distinguish which job the event belongs to.
- On WebSocket disconnect, unsubscribe and clean up the Redis connection.
- Handle `WebSocketDisconnect` exception gracefully.
- Add the WebSocket router to `app/routes/__init__.py` and register it in `app/main.py`.
- If Redis is unavailable, accept the connection and immediately send an error frame, then close with code 1011 (internal error).
**Verify:** `cd packages/api && pytest tests/unit/routes/test_ws_routes.py -x`

### Step 6: [DONE] Frontend WebSocket hook
**Files:** `packages/web/lib/useBriefProgress.ts`, `packages/web/lib/types/progress.ts`
**Tests:** `packages/web/__tests__/unit/useBriefProgress.test.ts`
**What to do:** Create a TypeScript type and React hook:
- `packages/web/lib/types/progress.ts` — `ProgressEvent` type matching the API schema: `{ job_id, brief_id, status, phase, progress_pct, message, timestamp }`.
- `useBriefProgress(briefId: string | null)` hook that:
  - Returns `{ events: Map<string, ProgressEvent>, isConnected }` — keyed by `job_id` so the UI can show per-job progress for all jobs in the brief.
  - Opens a WebSocket to `ws://<API_HOST>/ws/briefs/{briefId}/progress` when `briefId` is non-null.
  - Parses incoming JSON messages and upserts into the events map by `job_id`.
  - Closes the connection on unmount or when `briefId` changes.
  - Handles reconnection with exponential backoff (max 3 retries, 1s/2s/4s delays).
  - Uses `NEXT_PUBLIC_API_WS_URL` env var for the WebSocket base URL.
**Verify:** `cd packages/web && npx vitest run __tests__/unit/useBriefProgress.test.ts`

## Validation
- All unit tests pass: `cd packages/api && pytest -x` and `cd packages/web && npx vitest run`
- Lint passes: `cd packages/api && ruff check .` and `cd packages/web && npx eslint .`
- Enforcement passes: `bash enforcement/run-all.sh`
- Manual integration test: start docker compose, create a render job via API, connect to WebSocket endpoint with `wscat -c ws://localhost:8000/ws/briefs/{brief_id}/progress`, verify progress messages arrive as the job processes (each message includes `job_id` and `progress_pct`)

## Decision Log
(Populated during implementation)
