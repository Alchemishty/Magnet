# Repository Layer Implementation Plan

**Goal:** Implement CRUD data-access repositories for all six core models (User, Project, GameProfile, Asset, CreativeBrief, RenderJob), each accepting a SQLAlchemy Session and providing create, get_by_id, list, update, and delete methods.

**Architecture:** Repositories sit between Schemas and Services in the API layer stack. They depend on Models and Schemas only — no upward imports to Services, Agents, or Routes. A generic `BaseRepository[T]` class provides shared CRUD logic; concrete repositories inherit from it and add entity-specific filters or queries. All DB errors are caught and translated to domain errors at the repository boundary.

## Assumptions

- The synchronous SQLAlchemy `Session` (not async) is used, matching the existing `db.py` setup.
- `BaseModel` (the SQLAlchemy abstract base in `app/models/base.py`) provides `id`, `created_at`, and `updated_at` on all entities.
- Pydantic `*Create` schemas map directly to model constructor kwargs for simple creation.
- Pydantic `*Update` schemas use `model_dump(exclude_unset=True)` to produce partial-update dicts.
- `delete` performs a hard delete for now; soft-delete can be added later via a decision record.
- Integration tests require a running PostgreSQL instance and `TEST_DATABASE_URL` env var (existing conftest pattern).

## Open Questions

- None currently. Soft-delete and pagination strategy can be addressed in follow-up plans.

## Context and Orientation

- **Files to read before starting:**
  - `packages/api/app/db.py` — session factory and `get_db` dependency
  - `packages/api/app/models/base.py` — `BaseModel` with `id`, `created_at`, `updated_at`
  - `packages/api/app/models/*.py` — all six ORM models
  - `packages/api/app/schemas/*.py` — all Pydantic Create/Read/Update schemas
  - `packages/api/tests/integration/conftest.py` — `db_engine` and `db_session` fixtures
  - `packages/api/tests/helpers/factories.py` — test data builders
- **Patterns to follow:** conventions.md — snake_case files, PascalCase classes, absolute `app.` imports, typed errors, Arrange-Act-Assert tests
- **Related decisions:** None yet (this is the first repository implementation)
- **Similar existing code:** `tests/helpers/factories.py` shows model instantiation patterns; `tests/integration/conftest.py` shows transactional test session pattern

## Steps

### Step 1: Base repository with common CRUD operations ✅

**Files:**
- `packages/api/app/repositories/__init__.py`
- `packages/api/app/repositories/base.py`
- `packages/api/app/errors.py`

**Tests:**
- `packages/api/tests/unit/repositories/__init__.py`
- `packages/api/tests/unit/repositories/test_base.py`
- `packages/api/tests/integration/repositories/__init__.py`

**What to do:**

1. Create `packages/api/app/errors.py` with domain error classes: `DatabaseError`, `NotFoundError`. `DatabaseError` wraps SQLAlchemy errors. `NotFoundError` takes an entity name and ID.

2. Create `packages/api/app/repositories/base.py` with a generic `BaseRepository[T]` class:
   - `__init__(self, session: Session, model_class: type[T])` — stores session and model class.
   - `create(self, data: dict) -> T` — instantiates model, adds to session, flushes, returns instance. Wraps `SQLAlchemyError` in `DatabaseError`.
   - `get_by_id(self, entity_id: UUID) -> T | None` — `session.get(model_class, entity_id)`. Returns `None` if not found. Wraps errors.
   - `list(self, filters: dict | None = None, offset: int = 0, limit: int = 100) -> list[T]` — queries with optional column equality filters, applies offset/limit. Wraps errors.
   - `update(self, entity_id: UUID, data: dict) -> T | None` — fetches by ID, applies non-None values from `data` via `setattr`, flushes, returns updated instance or `None` if not found. Wraps errors.
   - `delete(self, entity_id: UUID) -> bool` — fetches by ID, deletes if found, flushes, returns `True`/`False`. Wraps errors.

3. Create `packages/api/app/repositories/__init__.py` that exports `BaseRepository`.

4. Create unit tests in `packages/api/tests/unit/repositories/test_base.py`:
   - Use `unittest.mock.MagicMock` for the SQLAlchemy Session.
   - Create a dummy SQLAlchemy model class for testing (or use `User` since models have no upward deps).
   - Test each method: `test_create_adds_and_flushes`, `test_get_by_id_returns_entity`, `test_get_by_id_returns_none`, `test_list_returns_all`, `test_list_with_filters`, `test_list_with_offset_limit`, `test_update_applies_changes`, `test_update_returns_none_when_not_found`, `test_delete_returns_true`, `test_delete_returns_false_when_not_found`, `test_create_wraps_sqlalchemy_error`.

**Verify:**
```bash
cd packages/api && ruff check .
cd packages/api && pytest tests/unit/repositories/test_base.py -v
```

---

### Step 2: UserRepository ✅

**Files:**
- `packages/api/app/repositories/user_repository.py`

**Tests:**
- `packages/api/tests/unit/repositories/test_user_repository.py`
- `packages/api/tests/integration/repositories/test_user_repository.py`

**What to do:**

1. Create `packages/api/app/repositories/user_repository.py`:
   - `class UserRepository(BaseRepository[User])` with `__init__(self, session: Session)` that calls `super().__init__(session, User)`.
   - Add `get_by_email(self, email: str) -> User | None` — queries `User` filtered by `email`.
   - Add `get_by_clerk_id(self, clerk_id: str) -> User | None` — queries `User` filtered by `clerk_id`.
   - Add `create_from_schema(self, schema: UserCreate) -> User` — calls `self.create(schema.model_dump())`.
   - Add `update_from_schema(self, entity_id: UUID, schema: UserUpdate) -> User | None` — calls `self.update(entity_id, schema.model_dump(exclude_unset=True))`.

2. Unit tests (`test_user_repository.py` in `tests/unit/repositories/`):
   - Mock Session. Test `get_by_email`, `get_by_clerk_id`, `create_from_schema`, `update_from_schema`.

3. Integration tests (`test_user_repository.py` in `tests/integration/repositories/`):
   - Mark with `@pytest.mark.integration`.
   - Use `db_session` fixture from conftest.
   - Test full round-trip: create a user, get_by_id, get_by_email, update, list, delete.
   - Test `get_by_email` returns `None` for nonexistent email.

4. Update `packages/api/app/repositories/__init__.py` to export `UserRepository`.

**Verify:**
```bash
cd packages/api && ruff check .
cd packages/api && pytest tests/unit/repositories/test_user_repository.py -v
cd packages/api && pytest tests/integration/repositories/test_user_repository.py -v
```

---

### Step 3: ProjectRepository + GameProfileRepository ✅

**Files:**
- `packages/api/app/repositories/project_repository.py`
- `packages/api/app/repositories/game_profile_repository.py`

**Tests:**
- `packages/api/tests/unit/repositories/test_project_repository.py`
- `packages/api/tests/unit/repositories/test_game_profile_repository.py`
- `packages/api/tests/integration/repositories/test_project_repository.py`
- `packages/api/tests/integration/repositories/test_game_profile_repository.py`

**What to do:**

1. Create `packages/api/app/repositories/project_repository.py`:
   - `class ProjectRepository(BaseRepository[Project])` with `__init__(self, session: Session)`.
   - Add `list_by_user(self, user_id: UUID, offset: int = 0, limit: int = 100) -> list[Project]` — filters by `user_id`.
   - Add `create_from_schema(self, schema: ProjectCreate) -> Project`.
   - Add `update_from_schema(self, entity_id: UUID, schema: ProjectUpdate) -> Project | None`.

2. Create `packages/api/app/repositories/game_profile_repository.py`:
   - `class GameProfileRepository(BaseRepository[GameProfile])` with `__init__(self, session: Session)`.
   - Add `get_by_project_id(self, project_id: UUID) -> GameProfile | None` — filters by `project_id` (unique constraint means at most one).
   - Add `create_from_schema(self, schema: GameProfileCreate) -> GameProfile`.
   - Add `update_from_schema(self, entity_id: UUID, schema: GameProfileUpdate) -> GameProfile | None`.

3. Unit tests: mock Session, test `list_by_user`, `get_by_project_id`, schema-based create/update for both repos.

4. Integration tests (marked `@pytest.mark.integration`):
   - ProjectRepository: create user first (FK dependency), then create project, list_by_user, update, delete.
   - GameProfileRepository: create user + project, then create game profile, get_by_project_id, update, delete.

5. Update `packages/api/app/repositories/__init__.py` to export both.

**Verify:**
```bash
cd packages/api && ruff check .
cd packages/api && pytest tests/unit/repositories/test_project_repository.py tests/unit/repositories/test_game_profile_repository.py -v
cd packages/api && pytest tests/integration/repositories/test_project_repository.py tests/integration/repositories/test_game_profile_repository.py -v
```

---

### Step 4: AssetRepository ✅

**Files:**
- `packages/api/app/repositories/asset_repository.py`

**Tests:**
- `packages/api/tests/unit/repositories/test_asset_repository.py`
- `packages/api/tests/integration/repositories/test_asset_repository.py`

**What to do:**

1. Create `packages/api/app/repositories/asset_repository.py`:
   - `class AssetRepository(BaseRepository[Asset])` with `__init__(self, session: Session)`.
   - Add `list_by_project(self, project_id: UUID, asset_type: str | None = None, offset: int = 0, limit: int = 100) -> list[Asset]` — filters by `project_id`, optionally also by `asset_type`.
   - Add `create_from_schema(self, schema: AssetCreate) -> Asset`.
   - Add `update_from_schema(self, entity_id: UUID, schema: AssetUpdate) -> Asset | None`.

2. Unit tests: mock Session, test `list_by_project` with and without `asset_type` filter, schema-based create/update.

3. Integration tests (marked `@pytest.mark.integration`):
   - Create user + project (FK chain), then create multiple assets with different types.
   - Test `list_by_project` returns all project assets, and filtered by `asset_type` returns subset.
   - Test get_by_id, update, delete.

4. Update `packages/api/app/repositories/__init__.py` to export `AssetRepository`.

**Verify:**
```bash
cd packages/api && ruff check .
cd packages/api && pytest tests/unit/repositories/test_asset_repository.py -v
cd packages/api && pytest tests/integration/repositories/test_asset_repository.py -v
```

---

### Step 5: BriefRepository ✅

**Files:**
- `packages/api/app/repositories/brief_repository.py`

**Tests:**
- `packages/api/tests/unit/repositories/test_brief_repository.py`
- `packages/api/tests/integration/repositories/test_brief_repository.py`

**What to do:**

1. Create `packages/api/app/repositories/brief_repository.py`:
   - `class BriefRepository(BaseRepository[CreativeBrief])` with `__init__(self, session: Session)`.
   - Add `list_by_project(self, project_id: UUID, status: str | None = None, offset: int = 0, limit: int = 100) -> list[CreativeBrief]` — filters by `project_id`, optionally also by `status`.
   - Add `create_from_schema(self, schema: BriefCreate) -> CreativeBrief`.
   - Add `update_from_schema(self, entity_id: UUID, schema: BriefUpdate) -> CreativeBrief | None`.

2. Unit tests: mock Session, test `list_by_project` with and without `status` filter, schema-based create/update.

3. Integration tests (marked `@pytest.mark.integration`):
   - Create user + project (FK chain), then create multiple briefs with different statuses.
   - Test `list_by_project` with status filter.
   - Test full CRUD round-trip including update that changes status from `draft` to `approved`.

4. Update `packages/api/app/repositories/__init__.py` to export `BriefRepository`.

**Verify:**
```bash
cd packages/api && ruff check .
cd packages/api && pytest tests/unit/repositories/test_brief_repository.py -v
cd packages/api && pytest tests/integration/repositories/test_brief_repository.py -v
```

---

### Step 6: RenderJobRepository ✅

**Files:**
- `packages/api/app/repositories/job_repository.py`

**Tests:**
- `packages/api/tests/unit/repositories/test_job_repository.py`
- `packages/api/tests/integration/repositories/test_job_repository.py`

**What to do:**

1. Create `packages/api/app/repositories/job_repository.py`:
   - `class RenderJobRepository(BaseRepository[RenderJob])` with `__init__(self, session: Session)`.
   - Add `list_by_brief(self, brief_id: UUID, status: str | None = None, offset: int = 0, limit: int = 100) -> list[RenderJob]` — filters by `brief_id`, optionally also by `status`.
   - Add `create_from_schema(self, schema: JobCreate) -> RenderJob`.
   - Add `update_from_schema(self, entity_id: UUID, schema: JobUpdate) -> RenderJob | None`.

2. Unit tests: mock Session, test `list_by_brief` with and without `status` filter, schema-based create/update.

3. Integration tests (marked `@pytest.mark.integration`):
   - Create full FK chain: user -> project -> brief -> render_job.
   - Test `list_by_brief` with and without status filter.
   - Test update that sets `status` to `"done"`, `output_s3_key`, and `render_duration_ms`.
   - Test update that sets `status` to `"failed"` with `error_message`.

4. Update `packages/api/app/repositories/__init__.py` to export `RenderJobRepository`.

**Verify:**
```bash
cd packages/api && ruff check .
cd packages/api && pytest tests/unit/repositories/test_job_repository.py -v
cd packages/api && pytest tests/integration/repositories/test_job_repository.py -v
```

## Validation

Run the full verification suite after all steps are complete:

```bash
# Lint
cd packages/api && ruff check .

# Format check
cd packages/api && ruff format --check .

# All unit tests
cd packages/api && pytest tests/unit/repositories/ -v

# All integration tests (requires TEST_DATABASE_URL)
cd packages/api && pytest tests/integration/repositories/ -v

# Full test suite
cd packages/api && pytest

# Enforcement checks
bash enforcement/run-all.sh
```

## Decision Log

(empty -- populated during implementation)
