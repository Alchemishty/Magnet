# QA Checklist: feat/websocket-progress

Generated: 2026-03-11
Branch: feat/websocket-progress
Changes: 17 files changed, 1678 insertions, 32 deletions

## Change-Specific QA

### WebSocket Endpoint
- [ ] Connect to `ws://localhost:8000/ws/briefs/{brief_id}/progress` with a valid brief UUID using wscat or similar tool — connection should be accepted
- [ ] Connect with an invalid UUID format — should return a 422 or reject the connection
- [ ] Disconnect the WebSocket client mid-stream — server should log debug message and clean up Redis subscription without errors
- [ ] Connect when Redis is not running — should receive a JSON error frame `{"error": "..."}` and connection should close with code 1011

### Progress Events from Render Task
- [ ] Create a render job via `POST /api/briefs/{brief_id}/jobs` while connected to the WebSocket — verify "rendering" event arrives with `progress_pct: 5`
- [ ] After a successful render completes — verify "done" event arrives with `progress_pct: 100`
- [ ] Force a render failure (e.g., missing brief) — verify "failed" event arrives with error message
- [ ] When Redis is unavailable during render — render task should complete normally (progress publishing is best-effort), no exceptions in Celery logs

### Multi-Job Tracking
- [ ] Create multiple render jobs for the same brief while connected — verify events arrive for each job with distinct `job_id` values
- [ ] Verify the `brief_id` field in each event matches the subscribed brief

### Frontend Hook
- [ ] `useBriefProgress(null)` returns empty events Map and `isConnected: false`, no WebSocket opened
- [ ] `useBriefProgress("valid-id")` opens a WebSocket connection to the correct URL
- [ ] When receiving multiple events for different jobs, the events Map keys by `job_id` and contains latest state per job
- [ ] On component unmount, WebSocket connection is closed
- [ ] On WebSocket close, hook retries up to 3 times with 1s/2s/4s backoff

### Redis Client
- [ ] `RedisClient.publish()` sends messages that are received by `RedisClient.subscribe()` on the same channel
- [ ] `RedisClient.subscribe()` with multiple channels receives messages from all subscribed channels
- [ ] `RedisClient.close()` properly closes the sync Redis connection
- [ ] `get_redis_client()` reads `REDIS_URL` env var, falls back to `CELERY_BROKER_URL`, then defaults to `redis://localhost:6379/0`

## Domain QA

### RenderJob
- [ ] Existing render job creation flow still works (`POST /api/briefs/{brief_id}/jobs`)
- [ ] Job status transitions (queued -> rendering -> done/failed) still persist correctly in PostgreSQL
- [ ] `GET /api/jobs/{job_id}` returns correct status after render completes
- [ ] `celery_task_id` is still stored on the job record

### CreativeBrief
- [ ] Brief lifecycle (draft -> approved -> producing -> complete) is unaffected by progress changes
- [ ] Existing brief CRUD endpoints still function

## Regression
- [ ] Existing tests pass (run: `cd packages/api && pytest`)
- [ ] Static analysis clean (run: `cd packages/api && ruff check .`)
- [ ] Web tests pass (run: `cd packages/web && npx vitest run`)
- [ ] Web lint clean (run: `cd packages/web && npx eslint .`)
- [ ] Enforcement rules pass (run: `bash enforcement/run-all.sh`)
- [ ] Application starts without errors (run: `docker compose up`)
