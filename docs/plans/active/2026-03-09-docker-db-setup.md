# Docker-Compose & Database Setup Implementation Plan

**Goal:** Get PostgreSQL, Redis, and MinIO running locally via docker-compose, wire FastAPI to the real database, verify the Alembic migration, and create pytest fixtures for integration tests against PostgreSQL.

**Architecture:** This is infrastructure + configuration work. It touches the API entry point (`main.py`), adds a database session module, configures Alembic to read from the environment, and creates shared test fixtures. No new business logic layers. The Dockerfile enables `docker compose up` for the full stack.

## Assumptions

- Docker and Docker Compose are installed on the dev machine
- PostgreSQL 16, Redis 7, MinIO as specified in the existing `docker-compose.yml`
- The existing `docker-compose.yml` is correct and only needs minor refinements (healthchecks)
- `.env` file already exists locally (gitignored) with `DATABASE_URL` etc.
- Alembic migration `001` already exists and is structurally correct
- No Dockerfile exists yet for `packages/api/` — needs to be created
- We use `asyncpg` for async DB access (SQLAlchemy async engine) — or stick with sync `psycopg2` for simplicity in MVP

## Open Questions

- None — the docker-compose.yml, .env.example, and alembic setup already define all the configuration values needed

## Context and Orientation

- **Files to read before starting:** `docker-compose.yml`, `.env.example`, `packages/api/app/main.py`, `packages/api/alembic.ini`, `packages/api/alembic/env.py`, `packages/api/pyproject.toml`
- **Patterns to follow:** `docs/conventions.md` — import ordering, error handling at boundaries
- **Related decisions:** `docs/decisions/001-initial-setup.md` — confirms PostgreSQL + SQLAlchemy + Docker Compose
- **Similar existing code:** `packages/api/app/models/base.py` (Base used by alembic env.py)

## Steps

### Step 1: [DONE] Database session module
**Files:**
- `packages/api/app/db.py` (create)
**Tests:**
- `packages/api/tests/unit/test_db.py` (create)
**What to do:**
Create a `db.py` module that configures the SQLAlchemy engine and sessionmaker. Read `DATABASE_URL` from environment (with a sensible default for local dev: `postgresql://magnet:magnet@localhost:5432/magnet`). Export a `get_db` dependency for FastAPI (yields a Session, closes on teardown). Export `engine` and `SessionLocal` for direct use in tests and Alembic. Use synchronous SQLAlchemy (psycopg2) for MVP simplicity.
Test: verify `get_db` yields a session-like object, verify `DATABASE_URL` is read from env.
**Verify:** `cd packages/api && pytest tests/unit/test_db.py`

### Step 2: [DONE] Wire FastAPI app to database
**Files:**
- `packages/api/app/main.py` (modify)
**Tests:**
- `packages/api/tests/unit/test_sanity.py` (modify — update if needed)
**What to do:**
Import `engine` from `app.db`. Add a startup event that logs the database URL (masked password). Add the `/health` endpoint to also verify DB connectivity by executing a simple `SELECT 1` query — return `{"status": "ok", "db": "connected"}` or `{"status": "ok", "db": "unreachable"}`. This makes it easy to verify the full stack is running.
**Verify:** `cd packages/api && pytest tests/unit/`

### Step 3: [DONE] Update Alembic to use app.db engine
**Files:**
- `packages/api/alembic/env.py` (modify)
**Tests:**
- (verified via migration run in step 6)
**What to do:**
Update `env.py` to import `DATABASE_URL` from `app.db` instead of reading `os.environ` directly. This ensures Alembic and the app always use the same connection config. Keep the `alembic.ini` URL as a fallback.
**Verify:** `cd packages/api && pytest tests/unit/test_migration.py`

### Step 4: [DONE] Dockerfiles for API and Web
**Files:**
- `packages/api/Dockerfile` (create)
- `packages/web/Dockerfile` (create)
**Tests:**
- (verified via docker compose build in step 5)
**What to do:**
Create a Dockerfile for `packages/api`: Python 3.10-slim base, install dependencies from `pyproject.toml` via pip, copy app code, expose port 8000, run `uvicorn app.main:app --host 0.0.0.0 --port 8000`. Create a Dockerfile for `packages/web`: Node 22-alpine base, install from package.json, copy source, expose port 3000, run `npm run dev` (dev mode for now).
**Verify:** `docker compose build api web`

### Step 5: [DONE] Docker-compose healthchecks and service readiness
**Files:**
- `docker-compose.yml` (modify)
**Tests:**
- (verified via docker compose up in step 6)
**What to do:**
Add healthchecks to PostgreSQL (`pg_isready`), Redis (`redis-cli ping`), and MinIO (`curl`). Add `depends_on` conditions so api/worker wait for postgres and redis to be healthy. Add a `test_db` service profile for integration tests — same postgres image but on port 5433 with a separate database name `magnet_test`. This avoids polluting the dev database during test runs.
**Verify:** `docker compose config` (validates compose file)

### Step 6: [DEFERRED] Verify Alembic migration against real PostgreSQL
**Files:**
- (no new files — verification step)
**Tests:**
- (manual verification)
**What to do:**
Start just the postgres service via `docker compose up -d postgres`. Wait for healthcheck. Run `cd packages/api && DATABASE_URL=postgresql://magnet:magnet@localhost:5432/magnet alembic upgrade head`. Verify all 6 tables were created by connecting with `psql` or running a quick Python script that inspects the database. Then run `alembic downgrade base` to verify the downgrade path. Then `alembic upgrade head` again to leave DB in migrated state.
**Verify:** `docker compose up -d postgres && sleep 3 && cd packages/api && alembic upgrade head`

### Step 7: [DONE] Integration test fixtures
**Files:**
- `packages/api/tests/conftest.py` (create)
- `packages/api/tests/integration/conftest.py` (create)
**Tests:**
- `packages/api/tests/integration/test_db_connection.py` (create)
**What to do:**
Create a root `conftest.py` that checks for a `TEST_DATABASE_URL` env var. Create an integration `conftest.py` with fixtures: `db_engine` (creates test engine, runs migrations up, yields engine, drops all tables after), `db_session` (yields a session wrapped in a transaction that rolls back after each test — fast isolation). Create a simple integration test that verifies: insert a User, query it back, confirm fields match. Mark integration tests with `@pytest.mark.integration` so they can be skipped when no DB is available.
**Verify:** `docker compose up -d postgres && cd packages/api && TEST_DATABASE_URL=postgresql://magnet:magnet@localhost:5432/magnet_test pytest tests/integration/ -v`

### Step 8: [DONE] Update .env.example with test database URL
**Files:**
- `.env.example` (modify)
**Tests:**
- (no tests needed)
**What to do:**
Add `TEST_DATABASE_URL=postgresql://magnet:magnet@localhost:5433/magnet_test` to `.env.example`. Add a comment section explaining the test database setup.
**Verify:** Visual check

## Validation

After all steps complete, run the full verification suite:
1. `bash enforcement/run-all.sh` — enforcement passes
2. `cd packages/api && ruff check .` — lint clean
3. `cd packages/api && pytest tests/unit/` — unit tests pass (no DB needed)
4. `docker compose up -d postgres` — PostgreSQL starts with healthcheck
5. `cd packages/api && alembic upgrade head` — migration applies cleanly
6. `cd packages/api && TEST_DATABASE_URL=... pytest tests/integration/` — integration tests pass
7. `docker compose build` — all Docker images build
8. `cd packages/web && npx eslint . && npx vitest run` — web unaffected

## Decision Log

- **Sync SQLAlchemy (psycopg2) for MVP:** Chose synchronous engine over async (asyncpg). Simpler, fewer footguns, and FastAPI supports sync dependencies fine. Can migrate to async later if needed.
- **Step 6 deferred:** Docker is not installed on the dev machine. Migration verification against real PostgreSQL will happen when Docker is available. The migration was structurally verified via unit tests.
- **test_db on separate port (5433):** Uses docker-compose profiles so the test DB only starts when explicitly requested (`--profile test`). Avoids polluting the dev database.
- **Transaction rollback per test:** Integration test fixture wraps each test in a transaction that rolls back. Fast isolation without table recreation.
