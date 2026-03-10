# Celery Task Integration Implementation Plan

**Goal:** Wire Celery tasks into the Magnet API so that creating a RenderJob dispatches an async Celery task that processes the job (queued → rendering → done/failed), providing the foundation for the video production pipeline.

**Architecture:** The tasks layer sits between services and the worker. When a job is created via the route, `JobService` dispatches a Celery task after persisting the job. The task runs in the Celery worker process, gets its own DB session, updates job status through the repository layer, and handles errors by marking jobs as failed. Worker configuration uses environment variables for broker/backend URLs.

## Assumptions
- Celery and Redis are already in `pyproject.toml` dependencies (confirmed: `celery>=5.3`, `redis>=5.0`)
- The render task will be a placeholder that simulates work — actual video pipeline logic comes in a later feature
- The worker process uses a separate DB session (not FastAPI's dependency injection)
- Task dispatch is fire-and-forget from the API's perspective — the client polls `GET /api/jobs/{id}` for status
- Import direction: tasks import from services/repositories, not the other way around

## Open Questions
- Should the Celery task ID be stored on the RenderJob model for correlation? (Useful for task revocation later, but adds a column now)
- Should we add a `celery_task_id` field to `JobRead` schema so clients can see it?

## Context and Orientation
- **Files to read before starting:** `app/worker.py`, `app/tasks/__init__.py`, `app/services/job_service.py`, `app/routes/jobs.py`, `app/models/job.py`, `app/schemas/job.py`, `app/db.py`, `app/errors.py`
- **Patterns to follow:** Provider abstraction pattern from `docs/conventions.md`; error handling at repository/service/route layers; test patterns from `tests/unit/services/test_job_service.py`
- **Related decisions:** None yet — this is the first Celery integration
- **Similar existing code:** `ConceptService.generate_concepts` shows the service-orchestrates pattern; `tests/unit/routes/test_job_routes.py` shows route test pattern with dependency overrides

## Steps

### Step 1: [DONE] Configure worker with environment variables
**Files:** `packages/api/app/worker.py`
**Tests:** `packages/api/tests/unit/test_worker.py`
**What to do:**
- Update `worker.py` to read `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` from environment variables with sensible defaults (current hardcoded values)
- Add `task_serializer` and `result_serializer` config set to `"json"`
- Add `task_track_started = True` so we can detect the rendering state
- Add autodiscover for `app.tasks` so task modules are auto-registered
- Write tests that verify the celery app is configured correctly (broker URL, serializer settings, autodiscover paths)
**Verify:** `cd packages/api && pytest tests/unit/test_worker.py -x`

### Step 2: [DONE] Create the render task
**Files:** `packages/api/app/tasks/render.py`
**Tests:** `packages/api/tests/unit/tasks/__init__.py`, `packages/api/tests/unit/tasks/test_render.py`
**What to do:**
- Create `render.py` with a `process_render_job` Celery task bound to the celery app from `worker.py`
- The task accepts `job_id: str` (UUID as string, since Celery serializes as JSON)
- Task flow: (1) get a DB session from `SessionLocal`, (2) fetch the job via `RenderJobRepository`, (3) update status to `"rendering"`, (4) simulate work (placeholder — just a pass or logging statement), (5) update status to `"done"`, (6) close the DB session in a finally block
- On any exception: update status to `"failed"` with `error_message` set to the exception string, then re-raise so Celery marks the task as failed
- Use `self.update_state` for Celery-level state tracking
- Tests: mock the DB session and repository. Test the happy path (status goes queued→rendering→done). Test the error path (exception → status set to failed, error_message populated). Test that the DB session is always closed (finally block).
**Verify:** `cd packages/api && pytest tests/unit/tasks/test_render.py -x`

### Step 3: [DONE] Add task dispatch to JobService
**Files:** `packages/api/app/services/job_service.py`
**Tests:** `packages/api/tests/unit/services/test_job_service.py`
**What to do:**
- Modify `JobService.create_job` to accept an optional `dispatch_task` callable (default `None`). After creating the job, if `dispatch_task` is not None, call `dispatch_task(str(job.id))`. This keeps the service testable without importing Celery directly.
- The route layer will inject the actual `process_render_job.delay` as the dispatch callable.
- Add tests: (1) when `dispatch_task` is provided, it's called with the job ID string after creation; (2) when `dispatch_task` is None (default), no dispatch happens and job is still created successfully; (3) if `dispatch_task` raises, the job is still created (fire-and-forget — log the error but don't fail the request).
**Verify:** `cd packages/api && pytest tests/unit/services/test_job_service.py -x`

### Step 4: [DONE] Wire task dispatch into the job creation route
**Files:** `packages/api/app/routes/jobs.py`, `packages/api/app/routes/dependencies.py`
**Tests:** `packages/api/tests/unit/routes/test_job_routes.py`
**What to do:**
- In `dependencies.py`, add a `get_task_dispatcher` dependency that returns `process_render_job.delay` (imported from `app.tasks.render`).
- In the `create_job` route, inject the task dispatcher via `Depends(get_task_dispatcher)` and pass it to `service.create_job(data, dispatch_task=dispatcher)`.
- Update route tests: the mock_service already mocks `create_job`, so just verify the dispatcher is passed through. Add a test that confirms the route still returns 201 even if task dispatch is part of the flow.
**Verify:** `cd packages/api && pytest tests/unit/routes/test_job_routes.py -x`

### Step 5: [DONE] Add celery_task_id to RenderJob model and schema
**Files:** `packages/api/app/models/job.py`, `packages/api/app/schemas/job.py`, `packages/api/app/tasks/render.py`
**Tests:** `packages/api/tests/unit/models/test_job.py`, `packages/api/tests/unit/schemas/test_job.py`
**What to do:**
- Add `celery_task_id: Mapped[str | None] = mapped_column(String(255))` to the `RenderJob` model
- Add `celery_task_id: str | None` to `JobRead` and `JobUpdate` schemas
- Update the render task to store `self.request.id` on the job record when it starts processing
- Update the service's dispatch flow: after calling `dispatch_task`, capture the AsyncResult and store its `.id` on the job via an update
- Update existing model/schema tests to include the new field
**Verify:** `cd packages/api && pytest tests/unit/models/test_job.py tests/unit/schemas/test_job.py tests/unit/tasks/test_render.py -x`

## Validation
- Run full test suite: `cd packages/api && pytest -x`
- Run linter: `cd packages/api && ruff check .`
- Run enforcement: `bash enforcement/run-all.sh`
- Expected: all tests pass, no lint errors, no enforcement violations
- Manual validation: creating a job via the API should return a 201 with `celery_task_id` field (null initially, populated when the worker picks it up)

## Decision Log
(This section starts empty. During implementation, decisions are recorded here.)
