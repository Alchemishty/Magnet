# Architecture

Magnet is a hybrid monorepo (Python + TypeScript) for agentic UA creative production. The Python backend handles API serving, agentic pipelines, video rendering, and background task processing. The TypeScript frontend provides a dashboard for project management, brief review, and creative preview. Layer boundaries described here are enforced mechanically via `enforcement/` rules.

---

## System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                                  │
│                    Next.js (TypeScript)                               │
│   Dashboard · Upload · Brief Review · Preview · Creative Library     │
└──────────────────────────┬───────────────────────────────────────────┘
                           │ REST / WebSocket
┌──────────────────────────▼───────────────────────────────────────────┐
│                      API GATEWAY                                     │
│                  FastAPI (Python)                                     │
│         Auth · Rate Limiting · Request Routing                       │
└──────────────────────────┬───────────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────────┐
│                   ORCHESTRATION LAYER                                 │
│                  Python (Celery + Redis)                              │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐     │
│  │              AGENTIC PIPELINE CONTROLLER                     │     │
│  │  Manages the flow: Concept → Production → QA → Delivery     │     │
│  └──────┬──────────────┬──────────────┬────────────────────────┘     │
│         │              │              │                               │
│  ┌──────▼──────┐ ┌─────▼──────┐ ┌────▼─────────┐                    │
│  │  Concept    │ │  Video     │ │  QA          │                     │
│  │  Agent      │ │  Agent     │ │  Agent       │                     │
│  │  (LLM)     │ │  (FFmpeg)  │ │  (LLM+CV)   │                     │
│  └─────────────┘ └────────────┘ └──────────────┘                     │
└──────────────────────────────────────────────────────────────────────┘
                           │
┌──────────────────────────▼───────────────────────────────────────────┐
│                      DATA LAYER                                      │
│  PostgreSQL        Redis           S3/MinIO        Vector DB         │
│  (metadata,        (queue,         (assets,        (Qdrant -         │
│   projects,        cache,          renders)        embeddings,       │
│   users)           sessions)                       later)            │
└──────────────────────────────────────────────────────────────────────┘
```

---

## API Layer Definitions (Python — packages/api/)

```
  ┌─────────────────────────┐
  │   Routes                │  ← HTTP handlers, request validation, response formatting
  ├─────────────────────────┤
  │   Agents                │  ← Agentic pipelines (Concept Agent, Video Agent)
  ├─────────────────────────┤
  │   Services              │  ← Business logic, orchestration, use cases
  ├─────────────────────────┤
  │   Repositories          │  ← Data access (DB queries, S3 ops, external API calls)
  ├─────────────────────────┤
  │   Schemas               │  ← Pydantic request/response models, validation
  ├─────────────────────────┤
  │   Models                │  ← SQLAlchemy ORM models, database table definitions
  └─────────────────────────┘
```

### Models (bottom layer)

SQLAlchemy ORM models defining database tables. No business logic.

- `packages/api/app/models/user.py` — User, Organization
- `packages/api/app/models/project.py` — Project, GameProfile
- `packages/api/app/models/asset.py` — Asset (gameplay, screenshots, logos, audio)
- `packages/api/app/models/brief.py` — CreativeBrief
- `packages/api/app/models/job.py` — RenderJob

Dependency rule: **Models depend on nothing** (SQLAlchemy base only).

### Schemas

Pydantic models for API request/response validation and serialization. Separate from ORM models.

Dependency rule: **Schemas depend on nothing** (may reference model field names but do not import models).

### Repositories

Data access layer. Each repository wraps one data source.

- `asset_repository.py` — S3 upload/download, presigned URLs
- `project_repository.py` — PostgreSQL CRUD for projects and game profiles
- `brief_repository.py` — PostgreSQL CRUD for creative briefs
- `job_repository.py` — PostgreSQL CRUD for render jobs

Dependency rule: **Repositories depend on Models and Schemas only.**

### Services

Business logic and orchestration.

- `project_service.py` — project creation, game profile management
- `brief_service.py` — brief lifecycle (draft → approved → producing → complete)
- `render_service.py` — render job creation, status tracking, output delivery

Dependency rule: **Services depend on Models, Schemas, and Repositories only.**

### Agents

Agentic pipeline orchestrators. Agents coordinate services and providers to execute multi-step AI workflows.

- `concept_agent.py` — STRATEGIZE → EXPAND → DIVERSIFY pipeline
- `video_agent.py` — PLAN → PREPARE → ASSEMBLE → POST-PROCESS pipeline

Dependency rule: **Agents depend on Models, Schemas, Services, and Providers.**

### Routes (top layer)

FastAPI route handlers. Thin — validate input, call service or agent, return response.

Dependency rule: **Routes depend on Schemas, Services, and Agents. Never import Repositories or Models directly.**

### Providers (cross-cutting)

Provider-agnostic interfaces for external services. Each provider implements a Protocol.

```
providers/
  base.py         # Protocol definitions (LLMProvider, TTSProvider, etc.)
  llm/            # Claude, OpenAI implementations
  tts/            # ElevenLabs, etc.
  music/          # Suno, etc.
  image/          # Image generation implementations
  video/          # Video generation implementations
```

Providers are injected into Services and Agents via configuration. They depend on Models/Schemas only.

### Rendering (cross-cutting)

FFmpeg assembly and programmatic template rendering.

- `assembler.py` — builds FFmpeg filter graphs from Composition JSON
- `composer.py` — orchestrates scene preparation (trim, crop, resize)
- `templates/` — programmatic scene renderers (text hooks, endcards, fake gameplay)

Rendering depends on Models and Providers.

---

## Web Layer Definitions (TypeScript — packages/web/)

```
  ┌─────────────────────────┐
  │   App (pages)           │  ← Next.js App Router pages and layouts
  ├─────────────────────────┤
  │   Components            │  ← React components (UI elements, forms, viewers)
  ├─────────────────────────┤
  │   Lib                   │  ← API client, hooks, utilities, state management
  ├─────────────────────────┤
  │   Models                │  ← TypeScript types/interfaces matching API schemas
  └─────────────────────────┘
```

Dependency rule: **App → Components → Lib → Models.** No upward imports.

---

## Dependency Rules Summary

### API (Python)

| Layer | May depend on | Must NOT depend on |
|-------|---------------|---------------------|
| Models | SQLAlchemy base only | Schemas, Repositories, Services, Agents, Routes |
| Schemas | Standard library, pydantic | Models, Repositories, Services, Agents, Routes |
| Repositories | Models, Schemas | Services, Agents, Routes |
| Services | Models, Schemas, Repositories | Agents, Routes |
| Agents | Models, Schemas, Services, Providers | Routes |
| Routes | Schemas, Services, Agents | Models, Repositories directly |

### Web (TypeScript)

| Layer | May depend on | Must NOT depend on |
|-------|---------------|---------------------|
| Models | Nothing (type definitions only) | Lib, Components, App |
| Lib | Models | Components, App |
| Components | Models, Lib | App |
| App | Models, Lib, Components | — |

---

## Data Flow

### Write Path (user creates a project and uploads assets)

```
User fills project form in Next.js
  → App page calls API client in lib/
    → POST /api/projects hits FastAPI route
      → project_service validates and creates project + game_profile
        → project_repository persists to PostgreSQL
          → Response returns project ID
            → User uploads assets via presigned S3 URLs
```

### Concept Generation Path

```
User triggers concept generation
  → POST /api/projects/:id/concepts
    → Route dispatches Celery task
      → Concept Agent runs STRATEGIZE → EXPAND → DIVERSIFY
        → LLM provider generates creative briefs
          → brief_repository persists briefs to PostgreSQL
            → WebSocket pushes progress to client
```

### Video Production Path

```
User approves brief, triggers production
  → POST /api/briefs/:id/produce
    → Route creates RenderJob, dispatches Celery task
      → Video Agent runs PLAN → PREPARE → ASSEMBLE → POST-PROCESS
        → PREPARE: parallel tasks (COMPOSE/GENERATE/RENDER scenes)
          → ASSEMBLE: FFmpeg builds final video from Composition JSON
            → POST-PROCESS: encode, thumbnail, upload to S3
              → WebSocket pushes completion to client
```

---

## External Service Integrations

| Service | Purpose | Layer |
|---------|---------|-------|
| PostgreSQL | Persistent data storage | Repository |
| Redis | Task queue (Celery), cache, WebSocket pub/sub | Repository / Infrastructure |
| S3 / MinIO | Asset and render storage | Repository (asset_repository) |
| LLM (Claude/OpenAI) | Concept generation, scene planning | Provider (llm/) |
| ElevenLabs | Text-to-speech voiceovers | Provider (tts/) |
| Suno | Music generation | Provider (music/) |
| Image gen models | AI-generated visual elements | Provider (image/) |
| Clerk | Authentication | Middleware |

---

## Entry Points

| Entry point | File | Platform | Purpose |
|-------------|------|----------|---------|
| API server | `packages/api/app/main.py` | Docker | FastAPI HTTP server |
| Celery worker | `packages/api/app/worker.py` | Docker | Background task processing |
| Web app | `packages/web/app/page.tsx` | Docker / Vercel | Next.js dashboard |

---

## Enforcement

Layer boundaries are enforced by:

1. **Import direction scripts** in `enforcement/` — separate checks for Python and TypeScript
2. **Code review automation** (CodeRabbit) that flags cross-layer imports
3. **Directory structure** that makes violations visually obvious

If you need to break a layer boundary, that is a signal to refactor.
