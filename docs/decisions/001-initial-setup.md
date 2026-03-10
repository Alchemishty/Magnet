# 001: Initial Project Setup

**Status:** accepted

**Context:** This project was bootstrapped as a greenfield project using the agent harness. The following technology choices were made during setup based on the design document (docs/plans/active/2026-03-09-agentic-ua-creative-platform-design.md).

**Decision:**
- Architecture: hybrid monorepo (Python + TypeScript)
- API / Agents / Workers: Python 3.10 + FastAPI + Celery
- Web Frontend: TypeScript + Next.js 14 (App Router)
- Database: PostgreSQL + SQLAlchemy
- Task Queue: Celery + Redis
- Object Storage: S3 / MinIO
- Video Assembly: FFmpeg
- Auth: Clerk
- Python linter: ruff
- TypeScript linter: eslint
- Python test framework: pytest
- TypeScript test framework: vitest
- Layer architecture: six-layer API (models → schemas → repositories → services → agents → routes), four-layer web (models → lib → components → app)
- Deployment: Docker Compose (dev), AWS ECS / Vercel (production)

**Alternatives considered:** None — these were selected during initial project setup based on project requirements and the design document.

**Consequences:**
- All future code must follow the conventions established in docs/conventions/.
- Architectural layer boundaries are enforced via import direction rules (separate for Python and TypeScript).
- Provider-agnostic interfaces required for all external services.
- These choices can be revisited by creating a new decision record that supersedes this one.
