# Local Development Setup Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the full stack runnable locally so the user can test the end-to-end flow (create project → upload assets → generate concepts → produce video) with `docker compose up postgres redis minio` for infra and native processes for the apps.

**Architecture:** Three code changes: add CORS middleware to the API, create a web `.env.local` with API URLs, and update `.env` with required config. Plus a startup script that orchestrates infra + migrations + all three processes.

**Tech Stack:** FastAPI (CORS), Next.js (env vars), shell script

---

## Assumptions
- Docker is installed and running (for Postgres, Redis, MinIO)
- User has an OpenAI API key in `.env` (already present)
- Python 3.10+ with `uv` and Node.js 20+ with `npm` are installed
- Ports 3000, 5432, 6379, 8000, 9000 are available

## Open Questions
- None.

## Context and Orientation
- **Files to read:** `packages/api/app/main.py` (add CORS), `.env` (update config), `packages/web/` (add .env.local)
- **Similar existing code:** None — this is infra/config work

## Steps

### Step 1: Add CORS middleware to the API

**Files:**
- Modify: `packages/api/app/main.py`

**Tests:** Existing API tests still pass.

**What to do:** Add FastAPI CORS middleware after the `app = FastAPI(...)` line. Allow origins `http://localhost:3000` (the Next.js dev server). Allow all methods and headers. Read allowed origins from `CORS_ORIGINS` env var with `http://localhost:3000` as default.

```python
from fastapi.middleware.cors import CORSMiddleware

cors_origins = os.environ.get("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Verify:** `cd packages/api && pytest -x`

---

### Step 2: Create web .env.local with API URLs

**Files:**
- Create: `packages/web/.env.local`

**Tests:** No tests needed — config file.

**What to do:** Create `packages/web/.env.local` with:
```
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_API_WS_URL=ws://localhost:8000
```

This file is already in `.gitignore` (`.env.local` pattern).

**Verify:** File exists and contains the correct values.

---

### Step 3: Update root .env with full local config

**Files:**
- Modify: `.env`

**Tests:** No tests needed — config file.

**What to do:** The current `.env` only has `OPENAI_API_KEY`. Add the remaining config needed for local dev. Keep the existing key, add:
```
DATABASE_URL=postgresql://magnet:magnet@localhost:5432/magnet
REDIS_URL=redis://localhost:6379/0
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
S3_BUCKET=magnet-assets
LLM_PROVIDER=openai
```

The `LLM_PROVIDER=openai` is critical — the default is `claude` which requires an Anthropic key the user doesn't have.

**Verify:** `grep LLM_PROVIDER .env` shows `openai`.

---

### Step 4: Create local dev startup script

**Files:**
- Create: `scripts/dev.sh`

**Tests:** No tests needed — startup script.

**What to do:** Create a shell script that starts the full local stack:
1. Start infra services: `docker compose up -d postgres redis minio`
2. Wait for Postgres to be healthy
3. Run DB migrations: `cd packages/api && uv run alembic upgrade head`
4. Start API server in background: `cd packages/api && uv run uvicorn app.main:app --reload`
5. Start Celery worker in background: `cd packages/api && uv run celery -A app.worker worker --loglevel=info`
6. Start web dev server: `cd packages/web && npm run dev`
7. Trap SIGINT to clean up background processes on Ctrl+C

The script should print clear status messages and the URLs to access:
```
Magnet Local Dev
  Web:  http://localhost:3000
  API:  http://localhost:8000
  MinIO: http://localhost:9001 (admin: minioadmin/minioadmin)
```

Make the script executable.

**Verify:** `bash scripts/dev.sh` starts all services (manual verification).

---

## Validation
1. Run `scripts/dev.sh`
2. Open `http://localhost:3000` — see the Magnet dashboard
3. Create a project, fill game profile
4. Upload an asset
5. Generate concepts — briefs appear (requires working LLM)
6. Approve a brief, trigger production
7. `cd packages/api && pytest -x` — API tests still pass
8. `cd packages/web && npx vitest run` — web tests still pass

## Decision Log
(Populated during implementation)
