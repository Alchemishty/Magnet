# API Routes + Services Layer Implementation Plan

**Goal:** Wire all existing repositories and the concept agent to FastAPI HTTP endpoints via a thin services layer, making the backend usable over HTTP.
**Architecture:** Services sit between routes and repositories, handling business logic (e.g., creating a project+game_profile atomically, triggering concept generation and persisting results). Routes are thin — validate input, call a service, return a response. Both layers use FastAPI dependency injection for DB sessions. Import direction: routes → services → repositories (routes never import repositories directly).

## Assumptions
- All 6 repositories exist and are tested (User, Project, GameProfile, Asset, Brief, Job)
- All Create/Read/Update schemas exist for every entity
- The ConceptAgent class exists with `generate_briefs(game_profile) -> list[BriefCreate]`
- `app.db.get_db()` yields a SQLAlchemy Session via FastAPI `Depends`
- `app.errors.NotFoundError` and `app.errors.DatabaseError` exist
- No auth middleware yet — MVP endpoints are unauthenticated (auth is a future step)
- No Celery yet — concept generation runs synchronously in the request (async later)

## Open Questions
- None — all required infrastructure is in place.

## Context and Orientation
- **Files to read before starting:** `app/db.py`, `app/errors.py`, `app/repositories/base.py`, `app/schemas/project.py`, `app/agents/concept_agent.py`, `docs/conventions.md` (error handling section)
- **Patterns to follow:** Error handling pattern from `docs/conventions.md` — routes catch service errors and map to HTTPException; services raise domain errors
- **Similar existing code:** Repository layer pattern (thin wrappers with schema helpers)

## Steps

### Step 1: [DONE] Add service errors
**Files:** `packages/api/app/errors.py`
**Tests:** `packages/api/tests/unit/test_errors.py`
**What to do:** Add `ValidationError` (for business rule violations like "GameProfile required before concept generation") to the existing errors module. Keep `NotFoundError` and `DatabaseError` as-is.
**Verify:** `cd packages/api && pytest tests/unit/test_errors.py -x`

### Step 2: [DONE] Project service
**Files:** `packages/api/app/services/project_service.py`
**Tests:** `packages/api/tests/unit/services/test_project_service.py`
**What to do:** Create `ProjectService` class that takes a `Session` in `__init__`. Methods:
- `create_project(data: ProjectCreate) -> Project` — creates project via ProjectRepository
- `get_project(project_id: UUID) -> Project` — raises `NotFoundError` if not found
- `list_projects(user_id: UUID, offset, limit) -> list[Project]`
- `update_project(project_id: UUID, data: ProjectUpdate) -> Project` — raises `NotFoundError` if not found
- `delete_project(project_id: UUID) -> None` — raises `NotFoundError` if not found
- `create_game_profile(data: GameProfileCreate) -> GameProfile` — verifies project exists first
- `get_game_profile(project_id: UUID) -> GameProfile` — raises `NotFoundError` if not found
- `update_game_profile(project_id: UUID, data: GameProfileUpdate) -> GameProfile`

Each method creates the appropriate repository internally. Tests use a real SQLAlchemy session with in-memory SQLite or mock the session.
**Verify:** `cd packages/api && pytest tests/unit/services/test_project_service.py -x`

### Step 3: [DONE] Brief service
**Files:** `packages/api/app/services/brief_service.py`
**Tests:** `packages/api/tests/unit/services/test_brief_service.py`
**What to do:** Create `BriefService` class that takes a `Session` in `__init__`. Methods:
- `list_briefs(project_id: UUID, status: str | None, offset, limit) -> list[CreativeBrief]`
- `get_brief(brief_id: UUID) -> CreativeBrief` — raises `NotFoundError`
- `update_brief(brief_id: UUID, data: BriefUpdate) -> CreativeBrief` — raises `NotFoundError`
- `delete_brief(brief_id: UUID) -> None` — raises `NotFoundError`
**Verify:** `cd packages/api && pytest tests/unit/services/test_brief_service.py -x`

### Step 4: [DONE] Concept service
**Files:** `packages/api/app/services/concept_service.py`
**Tests:** `packages/api/tests/unit/services/test_concept_service.py`
**What to do:** Create `ConceptService` class that takes a `Session` and an `LLMProvider` in `__init__`. Methods:
- `generate_concepts(project_id: UUID) -> list[CreativeBrief]` — fetches GameProfile (raises `NotFoundError` if missing), runs `ConceptAgent.generate_briefs()`, persists each returned `BriefCreate` via `BriefRepository`, returns persisted briefs.

Business rule: project must have a GameProfile to generate concepts (raise `ValidationError` if not).
Tests use `MockLLMProvider` from `tests/helpers/mocks.py`.
**Verify:** `cd packages/api && pytest tests/unit/services/test_concept_service.py -x`

### Step 5: [DONE] Asset service
**Files:** `packages/api/app/services/asset_service.py`
**Tests:** `packages/api/tests/unit/services/test_asset_service.py`
**What to do:** Create `AssetService` class that takes a `Session` in `__init__`. Methods:
- `create_asset(data: AssetCreate) -> Asset` — verifies project exists
- `list_assets(project_id: UUID, asset_type: str | None, offset, limit) -> list[Asset]`
- `get_asset(asset_id: UUID) -> Asset` — raises `NotFoundError`
- `delete_asset(asset_id: UUID) -> None` — raises `NotFoundError`
**Verify:** `cd packages/api && pytest tests/unit/services/test_asset_service.py -x`

### Step 6: [DONE] Job service
**Files:** `packages/api/app/services/job_service.py`
**Tests:** `packages/api/tests/unit/services/test_job_service.py`
**What to do:** Create `JobService` class that takes a `Session` in `__init__`. Methods:
- `create_job(data: JobCreate) -> RenderJob` — verifies brief exists
- `list_jobs(brief_id: UUID, status: str | None, offset, limit) -> list[RenderJob]`
- `get_job(job_id: UUID) -> RenderJob` — raises `NotFoundError`
- `update_job(job_id: UUID, data: JobUpdate) -> RenderJob` — raises `NotFoundError`
**Verify:** `cd packages/api && pytest tests/unit/services/test_job_service.py -x`

### Step 7: [DONE] Services __init__ exports
**Files:** `packages/api/app/services/__init__.py`
**Tests:** None (verified by import in later steps)
**What to do:** Export all service classes from the services package:
```python
from app.services.project_service import ProjectService
from app.services.brief_service import BriefService
from app.services.concept_service import ConceptService
from app.services.asset_service import AssetService
from app.services.job_service import JobService
```
**Verify:** `cd packages/api && python -c "from app.services import ProjectService, BriefService, ConceptService, AssetService, JobService"`

### Step 8: [DONE] Route dependencies
**Files:** `packages/api/app/routes/dependencies.py`
**Tests:** None (tested through route tests)
**What to do:** Create FastAPI dependency functions:
- `get_project_service(db: Session = Depends(get_db)) -> ProjectService`
- `get_brief_service(db: Session = Depends(get_db)) -> BriefService`
- `get_concept_service(db: Session = Depends(get_db)) -> ConceptService` — needs an LLMProvider; for now use a placeholder that raises NotImplementedError (real provider comes in a future step)
- `get_asset_service(db: Session = Depends(get_db)) -> AssetService`
- `get_job_service(db: Session = Depends(get_db)) -> JobService`
**Verify:** `cd packages/api && python -c "from app.routes.dependencies import get_project_service"`

### Step 9: [DONE] Project routes
**Files:** `packages/api/app/routes/projects.py`
**Tests:** `packages/api/tests/unit/routes/test_project_routes.py`
**What to do:** Create `APIRouter` with prefix `/api/projects`. Endpoints:
- `POST /api/projects` — create project, return `ProjectRead`
- `GET /api/projects?user_id=` — list projects for a user
- `GET /api/projects/{project_id}` — get project by ID
- `PATCH /api/projects/{project_id}` — update project
- `DELETE /api/projects/{project_id}` — delete project
- `POST /api/projects/{project_id}/game-profile` — create game profile
- `GET /api/projects/{project_id}/game-profile` — get game profile
- `PATCH /api/projects/{project_id}/game-profile` — update game profile

Use `Depends(get_project_service)`. Catch `NotFoundError` → 404, `DatabaseError` → 500.
Tests use FastAPI `TestClient` with dependency overrides.
**Verify:** `cd packages/api && pytest tests/unit/routes/test_project_routes.py -x`

### Step 10: [DONE] Brief + concept routes
**Files:** `packages/api/app/routes/briefs.py`
**Tests:** `packages/api/tests/unit/routes/test_brief_routes.py`
**What to do:** Create `APIRouter` with prefix `/api`. Endpoints:
- `GET /api/projects/{project_id}/briefs?status=` — list briefs for project
- `POST /api/projects/{project_id}/concepts` — trigger concept generation, return list of `BriefRead`
- `GET /api/briefs/{brief_id}` — get brief by ID
- `PATCH /api/briefs/{brief_id}` — update brief
- `DELETE /api/briefs/{brief_id}` — delete brief

Concept generation endpoint uses `ConceptService`. Other endpoints use `BriefService`.
Tests use `TestClient` with mocked services via dependency overrides.
**Verify:** `cd packages/api && pytest tests/unit/routes/test_brief_routes.py -x`

### Step 11: [DONE] Asset routes
**Files:** `packages/api/app/routes/assets.py`
**Tests:** `packages/api/tests/unit/routes/test_asset_routes.py`
**What to do:** Create `APIRouter` with prefix `/api`. Endpoints:
- `POST /api/projects/{project_id}/assets` — register an asset
- `GET /api/projects/{project_id}/assets?asset_type=` — list assets for project
- `GET /api/assets/{asset_id}` — get asset by ID
- `DELETE /api/assets/{asset_id}` — delete asset
**Verify:** `cd packages/api && pytest tests/unit/routes/test_asset_routes.py -x`

### Step 12: [DONE] Job routes
**Files:** `packages/api/app/routes/jobs.py`
**Tests:** `packages/api/tests/unit/routes/test_job_routes.py`
**What to do:** Create `APIRouter` with prefix `/api`. Endpoints:
- `POST /api/briefs/{brief_id}/jobs` — create a render job for a brief
- `GET /api/briefs/{brief_id}/jobs?status=` — list jobs for a brief
- `GET /api/jobs/{job_id}` — get job by ID
- `PATCH /api/jobs/{job_id}` — update job status
**Verify:** `cd packages/api && pytest tests/unit/routes/test_job_routes.py -x`

### Step 13: [DONE] Register routers in main.py
**Files:** `packages/api/app/main.py`, `packages/api/app/routes/__init__.py`
**Tests:** `packages/api/tests/unit/routes/test_router_registration.py`
**What to do:** Import all routers in `routes/__init__.py`. In `main.py`, include all routers via `app.include_router()`. Write a simple test that verifies all expected URL paths are registered on the app.
**Verify:** `cd packages/api && pytest tests/unit/routes/test_router_registration.py -x`

## Validation
- Run full test suite: `cd packages/api && pytest -x`
- Run linter: `cd packages/api && ruff check .`
- Run enforcement: `bash enforcement/run-all.sh`
- All ~270+ tests should pass (existing 220 + ~50 new)
- All API endpoints should appear in FastAPI auto-docs at `/docs`

## Decision Log
- ConceptService accepts a `generate_briefs_fn` callable instead of importing ConceptAgent directly, to respect the architecture's import direction (services cannot import agents)
- Concept generation route returns 501 ("LLM provider not configured") as a placeholder until a real LLM provider is wired in
- Route dependencies use generator functions (`yield`) for consistency with FastAPI's DI lifecycle
- ConceptService validates that GameProfile has genre and target_audience before generating concepts
