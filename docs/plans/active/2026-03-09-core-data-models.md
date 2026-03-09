# Core Data Models & Database Schema Implementation Plan

**Goal:** Implement SQLAlchemy models, Pydantic schemas, and Alembic migration for all MVP entities — User, Project, GameProfile, Asset, CreativeBrief, and RenderJob — establishing the data foundation for the entire platform.

**Status:** Implementation complete — all 9 steps done, 90 tests passing.

**Architecture:** This touches the two bottom API layers only: Models (SQLAlchemy ORM) and Schemas (Pydantic). Models define database tables with no business logic. Schemas define API request/response shapes and validation, independent of models. Alembic manages migrations. All enum values stored as strings. Composition JSON stored as PostgreSQL JSONB. UUIDs for all primary keys.

## Assumptions

- PostgreSQL is the target database (per design doc and decision 001)
- No database is running yet — Alembic migration will be generated but tested structurally, not against a live DB
- UUID primary keys (standard for distributed systems, no auto-increment conflicts)
- `created_at` / `updated_at` timestamps on all tables
- Single-user MVP — no org/team tables beyond a simple User model
- GameProfile is 1:1 with Project (embedded in the same lifecycle)
- Enums stored as PostgreSQL string types, not native PG enums (easier to extend)

## Open Questions

- None — the design doc and domain glossary fully specify the entity fields and relationships

## Context and Orientation

- **Files to read before starting:** `docs/architecture.md` (layer definitions), `docs/domain.md` (entity fields and relationships), `docs/conventions.md` (naming), `docs/testing.md` (test patterns and factories)
- **Patterns to follow:** `docs/conventions.md` — naming (snake_case columns, PascalCase classes), import ordering, serialization rules (enums as strings, dates as ISO 8601 UTC)
- **Related decisions:** `docs/decisions/001-initial-setup.md` — confirms SQLAlchemy + PostgreSQL
- **Similar existing code:** `packages/api/app/main.py` (FastAPI entry), `packages/api/app/providers/base.py` (Protocol pattern)

## Steps

### Step 1: [DONE] SQLAlchemy base and database configuration
**Files:**
- `packages/api/app/models/base.py` (create)
- `packages/api/app/models/__init__.py` (modify — re-export Base)
**Tests:**
- `packages/api/tests/unit/models/test_base.py` (create)
**What to do:**
Create a declarative base with common columns: `id` (UUID, default=uuid4, primary key), `created_at` (DateTime, server_default=now), `updated_at` (DateTime, onupdate=now). All models will inherit from this base. Define a `BaseModel` class (not to be confused with Pydantic) that includes these common columns. Export `Base` and `BaseModel` from `__init__.py`.
**Verify:** `cd packages/api && pytest tests/unit/models/`

### Step 2: [DONE] User model
**Files:**
- `packages/api/app/models/user.py` (create)
- `packages/api/app/models/__init__.py` (modify — add User to exports)
**Tests:**
- `packages/api/tests/unit/models/test_user.py` (create)
**What to do:**
Create `User` model inheriting from `BaseModel`. Fields: `email` (String, unique, not null), `name` (String, not null), `clerk_id` (String, unique, nullable — external auth ID), `role` (String, default="creator"). Add relationship to `projects` (one-to-many). Test: model instantiation, field defaults, required fields.
**Verify:** `cd packages/api && pytest tests/unit/models/`

### Step 3: [DONE] Project and GameProfile models
**Files:**
- `packages/api/app/models/project.py` (create)
- `packages/api/app/models/__init__.py` (modify — add Project, GameProfile)
**Tests:**
- `packages/api/tests/unit/models/test_project.py` (create)
**What to do:**
Create `Project` model: `user_id` (UUID, FK to users.id, not null), `name` (String, not null), `status` (String, default="active"). Relationships: belongs to User, has one GameProfile, has many Assets, has many CreativeBriefs.
Create `GameProfile` model: `project_id` (UUID, FK to projects.id, unique, not null), `genre` (String), `target_audience` (String), `core_mechanics` (ARRAY of String or JSON), `art_style` (String), `brand_guidelines` (JSONB), `competitors` (ARRAY of String or JSON), `key_selling_points` (ARRAY of String or JSON). Relationship: belongs to Project (one-to-one).
Test: model instantiation, FK relationships, JSONB fields accept dicts.
**Verify:** `cd packages/api && pytest tests/unit/models/`

### Step 4: [DONE] Asset model
**Files:**
- `packages/api/app/models/asset.py` (create)
- `packages/api/app/models/__init__.py` (modify — add Asset)
**Tests:**
- `packages/api/tests/unit/models/test_asset.py` (create)
**What to do:**
Create `Asset` model: `project_id` (UUID, FK to projects.id, not null), `asset_type` (String, not null — "gameplay", "screenshot", "logo", "character", "audio"), `s3_key` (String, not null), `filename` (String, not null), `content_type` (String), `size_bytes` (BigInteger), `duration_ms` (Integer, nullable — for video/audio), `width` (Integer, nullable), `height` (Integer, nullable), `metadata` (JSONB, default={}). Relationship: belongs to Project.
Test: model instantiation, nullable fields, metadata defaults.
**Verify:** `cd packages/api && pytest tests/unit/models/`

### Step 5: [DONE] CreativeBrief model
**Files:**
- `packages/api/app/models/brief.py` (create)
- `packages/api/app/models/__init__.py` (modify — add CreativeBrief)
**Tests:**
- `packages/api/tests/unit/models/test_brief.py` (create)
**What to do:**
Create `CreativeBrief` model: `project_id` (UUID, FK to projects.id, not null), `hook_type` (String — from hook taxonomy), `narrative_angle` (String), `script` (Text), `voiceover_text` (Text, nullable), `target_emotion` (String), `cta_text` (String), `reference_ads` (JSONB, default=[]), `target_format` (String, default="9:16"), `target_duration` (Integer, default=15 — seconds), `status` (String, default="draft" — draft/approved/producing/complete), `generated_by` (String, default="agent" — "agent" or "human"), `scene_plan` (JSONB, nullable — the scene-by-scene strategy plan). Relationships: belongs to Project, has many RenderJobs.
Test: model instantiation, status default, scene_plan accepts dict.
**Verify:** `cd packages/api && pytest tests/unit/models/`

### Step 6: [DONE] RenderJob model
**Files:**
- `packages/api/app/models/job.py` (create)
- `packages/api/app/models/__init__.py` (modify — add RenderJob)
**Tests:**
- `packages/api/tests/unit/models/test_job.py` (create)
**What to do:**
Create `RenderJob` model: `brief_id` (UUID, FK to creative_briefs.id, not null), `status` (String, default="queued" — queued/rendering/done/failed), `composition` (JSONB, nullable — the Composition JSON contract), `output_s3_key` (String, nullable), `render_duration_ms` (Integer, nullable), `error_message` (Text, nullable). Relationship: belongs to CreativeBrief.
Test: model instantiation, status default, composition accepts the documented JSON structure.
**Verify:** `cd packages/api && pytest tests/unit/models/`

### Step 7: [DONE] Pydantic schemas for all entities
**Files:**
- `packages/api/app/schemas/user.py` (create)
- `packages/api/app/schemas/project.py` (create)
- `packages/api/app/schemas/asset.py` (create)
- `packages/api/app/schemas/brief.py` (create)
- `packages/api/app/schemas/job.py` (create)
- `packages/api/app/schemas/composition.py` (create)
- `packages/api/app/schemas/__init__.py` (modify — re-export all schemas)
**Tests:**
- `packages/api/tests/unit/schemas/test_user.py` (create)
- `packages/api/tests/unit/schemas/test_project.py` (create)
- `packages/api/tests/unit/schemas/test_asset.py` (create)
- `packages/api/tests/unit/schemas/test_brief.py` (create)
- `packages/api/tests/unit/schemas/test_job.py` (create)
- `packages/api/tests/unit/schemas/test_composition.py` (create)
**What to do:**
For each entity, create `<Entity>Create` (input for creation), `<Entity>Read` (output with id and timestamps), and `<Entity>Update` (partial update, all fields optional) Pydantic models. For `composition.py`, create typed schemas matching the Composition JSON contract: `CompositionLayer` (with type, asset_id, content, start, end, position, effects, etc.) and `Composition` (duration, resolution, fps, layers). All schemas use `model_config = ConfigDict(from_attributes=True)` for ORM compatibility. Schemas must NOT import from `app.models`. Validate enums (status values, asset types, hook types) using Literal types.
Test: valid construction, validation errors on invalid input, `from_attributes` works with mock objects, enum validation rejects invalid values.
**Verify:** `cd packages/api && pytest tests/unit/schemas/`

### Step 8: [DONE] Test factories
**Files:**
- `packages/api/tests/helpers/factories.py` (modify — add factories for all models)
**Tests:**
- (factories are tested implicitly by the model and schema tests)
**What to do:**
Add factory functions following the pattern from `docs/testing.md`: `create_test_user()`, `create_test_project()`, `create_test_game_profile()`, `create_test_asset()`, `create_test_brief()`, `create_test_render_job()`. Each accepts `**overrides` and merges with sensible defaults. These will be used by all future tests.
**Verify:** `cd packages/api && pytest tests/unit/`

### Step 9: [DONE] Alembic setup and initial migration
**Files:**
- `packages/api/alembic.ini` (create)
- `packages/api/alembic/env.py` (create)
- `packages/api/alembic/script.py.mako` (create)
- `packages/api/alembic/versions/` (create directory)
**Tests:**
- `packages/api/tests/unit/test_migration.py` (create)
**What to do:**
Initialize Alembic configuration pointing to the SQLAlchemy Base metadata. Configure `env.py` to import all models (so autogenerate works) and read `DATABASE_URL` from environment. Generate the initial migration that creates all six tables with correct columns, constraints, foreign keys, and indexes. Test: verify the migration script exists and imports correctly (structural test — no live DB needed). Add an index on `creative_briefs.project_id` and `render_jobs.brief_id` for common query patterns.
**Verify:** `cd packages/api && pytest tests/unit/`

## Validation

After all steps complete, run the full verification suite from `harness.yaml`:
1. `bash enforcement/run-all.sh` — import direction, file size, no secrets
2. `cd packages/api && ruff check .` — lint passes
3. `cd packages/api && pytest` — all tests pass
4. `cd packages/web && npx eslint .` — web lint unaffected
5. `cd packages/web && npx vitest run` — web tests unaffected

Expected: all 6 model files, 6+ schema files, 8+ test files, 1 Alembic migration. All tests green. No import direction violations (models and schemas are the two bottom layers).

## Decision Log

- **Python-side defaults via `__init__`:** SQLAlchemy `mapped_column(default=...)` only applies at flush time, not at Python instantiation. Used `__init__` with `setdefault()` pattern so model instances have correct defaults immediately (e.g., `status="draft"` on CreativeBrief). Also set `server_default` for DB-level defaults.
- **`metadata_` attribute name:** SQLAlchemy reserves `metadata` as a class attribute on declarative bases. Used `metadata_` as the Python attribute with `mapped_column("metadata", ...)` to map to the `metadata` DB column.
- **JSONB list fields without ARRAY type:** Used JSONB instead of PostgreSQL ARRAY for `core_mechanics`, `competitors`, `key_selling_points` — more flexible, allows mixed types, and queryable via JSONB operators.
- **Manual migration:** Autogenerate requires a running DB. Wrote the initial migration by hand matching model definitions exactly. Will verify against real DB when docker-compose is up.
