# Magnet Development Guide

Magnet is an agentic AI platform for mobile game user acquisition (UA) creative production. It generates diverse creative concepts from game profiles and produces video ads through three strategies — COMPOSE real assets, GENERATE AI elements, and RENDER programmatic templates — assembled via FFmpeg.

## Quick Reference

| Topic | Doc |
|-------|-----|
| Architecture & data flow | [docs/architecture.md](docs/architecture.md) |
| Coding conventions | [docs/conventions.md](docs/conventions.md) |
| Domain concepts & glossary | [docs/domain.md](docs/domain.md) |
| Testing strategy | [docs/testing.md](docs/testing.md) |
| Active plans | [docs/plans/active/](docs/plans/active/) |
| Decision records | [docs/decisions/](docs/decisions/) |
| Agent memory | [memory/](memory/) |

## Tech Stack

| Layer | Tech |
|-------|------|
| API / Agents | Python 3.10 + FastAPI |
| Web Frontend | TypeScript + Next.js 14 (App Router) |
| Task Queue | Celery + Redis |
| Database | PostgreSQL + SQLAlchemy |
| Object Storage | S3 / MinIO |
| Video Assembly | FFmpeg |
| Auth | Clerk |
| Styling | Tailwind + shadcn/ui |

## Commands

```bash
# API (Python)
cd packages/api && uv sync          # install dependencies
cd packages/api && ruff check .     # lint
cd packages/api && pytest           # test
cd packages/api && alembic upgrade head  # migrate

# Web (TypeScript)
cd packages/web && npm install      # install dependencies
cd packages/web && npx eslint .     # lint
cd packages/web && npx vitest run   # test
cd packages/web && npm run build    # build

# Full stack
docker compose build                # build all services
docker compose up                   # start all services
```

## Project Structure

```
magnet/
├── packages/
│   ├── api/                    # FastAPI backend + agents + workers
│   │   ├── app/
│   │   │   ├── main.py         # FastAPI entry point
│   │   │   ├── worker.py       # Celery worker entry point
│   │   │   ├── models/         # SQLAlchemy models
│   │   │   ├── schemas/        # Pydantic request/response schemas
│   │   │   ├── repositories/   # Data access (DB, S3, external APIs)
│   │   │   ├── services/       # Business logic and orchestration
│   │   │   ├── agents/         # Concept Agent, Video Agent
│   │   │   ├── providers/      # Provider-agnostic interfaces (LLM, TTS, music, image, video)
│   │   │   ├── rendering/      # FFmpeg assembler, programmatic templates
│   │   │   ├── routes/         # API route handlers
│   │   │   └── tasks/          # Celery task definitions
│   │   ├── alembic/            # Database migrations
│   │   └── tests/
│   ├── web/                    # Next.js frontend
│   │   ├── app/                # App Router pages
│   │   ├── components/         # React components
│   │   ├── lib/                # Utilities, API client, hooks
│   │   └── __tests__/
│   └── shared/                 # Shared types/constants
├── enforcement/                # Architectural rule scripts
├── docs/                       # Project documentation
├── scripts/                    # Utility scripts
└── docker-compose.yml
```

## Architecture Overview

Hybrid monorepo: Python backend (FastAPI + Celery) handles API, agentic pipelines, and video rendering. TypeScript frontend (Next.js) provides the dashboard. Services communicate via REST/WebSocket. See [docs/architecture.md](docs/architecture.md) for diagrams and data flow.

## Key Conventions

1. **Provider-agnostic interfaces** — all external services (LLM, TTS, music, image, video) use Protocol classes; swap via config
2. **Composition JSON** — the contract between AI (concept/scene planning) and rendering (FFmpeg assembly)
3. **Three scene strategies** — COMPOSE (real assets), GENERATE (AI-created), RENDER (programmatic)
4. **Import direction enforced** — API: models → schemas → repositories → services → agents → routes
5. **Package-namespaced commands** — always prefix with `api.` or `web.` in harness.yaml

See [docs/conventions.md](docs/conventions.md) for the complete guide.

## Domain Concepts

- **GameProfile** — genre, mechanics, audience, art style, brand guidelines for a mobile game
- **CreativeBrief** — hook type, narrative angle, script, scene plan — the blueprint for a video ad
- **RenderJob** — tracks video production from queued through rendering to delivery
- **Composition JSON** — layered timeline describing every element in a video ad
- **Hook Taxonomy** — categorized ad opening strategies (fail/challenge, satisfaction, comparison, etc.)

See [docs/domain.md](docs/domain.md) for the full glossary and business rules.

## Testing

Python: pytest with unit/integration split. TypeScript: vitest with unit tests. Both follow AAA pattern. Coverage target: 80%. See [docs/testing.md](docs/testing.md) for the full testing strategy.

## Context Management

Agents write learned patterns and recurring fixes to `memory/` for cross-session persistence. Verbose tool output (tests, lint, builds) goes to `scratch/` — keep only summaries in conversation context. For long tasks (7+ steps), use sub-agents to isolate context.

## Agent Rules

1. **Never commit secrets or credentials** — use environment variables
2. **Run verification before committing** — never skip the pre-commit gate
3. **Write tests before implementation** — TDD by default
4. **Follow docs/conventions.md** — consistency over preference
5. **Update docs when architecture changes** — keep docs/ in sync with reality
6. **Keep commits atomic** — one logical change per commit
7. **Record non-obvious decisions in docs/decisions/** — future agents need context
8. **Escalate to human when stuck after 3 retries** — don't spin endlessly
9. **Check harness.yaml for commands** — never hardcode tool invocations
10. **Read before modifying** — always read a file before editing it
