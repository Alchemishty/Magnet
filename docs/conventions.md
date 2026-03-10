# Coding Conventions

This document defines coding conventions for the Magnet monorepo. The Python (API) and TypeScript (Web) stacks each have language-specific rules. Shared principles apply to both.

---

## Import Ordering and Style

### Python (packages/api/)

```python
# 1. Standard library
import os
from datetime import datetime
from pathlib import Path

# 2. Third-party
import httpx
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import Column, String

# 3. Internal
from app.models.project import Project
from app.services.brief_service import BriefService
```

### TypeScript (packages/web/)

```typescript
// 1. Node built-ins
import path from 'node:path';

// 2. Third-party / framework
import React from 'react';
import { useQuery } from '@tanstack/react-query';

// 3. Internal
import { ProjectModel } from '@/models/project';
import { apiClient } from '@/lib/api-client';
```

### Rules

- Groups separated by a blank line. Alphabetical within groups.
- Remove unused imports — they fail CI.
- Prefer explicit imports over wildcards.
- Python: absolute imports from `app.` prefix. No relative imports across layers.
- TypeScript: use `@/` path alias for internal imports.

---

## Naming Conventions

### Python

| Thing | Convention | Example |
|-------|-----------|---------|
| Files | `snake_case.py` | `concept_agent.py`, `brief_service.py` |
| Classes | `PascalCase` | `CreativeBrief`, `ConceptAgent` |
| Functions / Methods | `snake_case` | `generate_concepts`, `get_brief_by_id` |
| Variables | `snake_case` | `render_job`, `total_duration` |
| Constants | `SCREAMING_SNAKE_CASE` | `MAX_RETRIES`, `DEFAULT_FPS` |
| Private | `_prefix` | `_build_filter_graph` |

### TypeScript

| Thing | Convention | Example |
|-------|-----------|---------|
| Files | `kebab-case.ts(x)` | `project-form.tsx`, `api-client.ts` |
| Types / Interfaces | `PascalCase` | `CreativeBrief`, `RenderJob` |
| Functions / Variables | `camelCase` | `fetchBriefs`, `projectId` |
| Constants | `SCREAMING_SNAKE_CASE` | `API_BASE_URL` |
| React components | `PascalCase` | `BriefCard`, `AssetUploader` |

### Shared

| Thing | Convention |
|-------|-----------|
| Database columns | `snake_case` — `created_at`, `asset_type` |
| JSON keys (API) | `snake_case` — `{ "hook_type": "...", "render_duration_ms": 0 }` |
| URL paths | `kebab-case` — `/api/projects/:id/creative-briefs` |
| Environment variables | `SCREAMING_SNAKE_CASE` — `DATABASE_URL`, `REDIS_URL` |
| Booleans | `is_`/`has_`/`can_` prefix — `is_approved`, `hasPermission` |

---

## Error Handling

### Python (API layer)

```python
# Routes: validate input, catch service errors, return HTTP responses
@router.post("/projects/{project_id}/concepts")
async def generate_concepts(project_id: str, service: ConceptService = Depends()):
    try:
        briefs = await service.generate(project_id)
        return {"briefs": briefs}
    except ProjectNotFoundError:
        raise HTTPException(status_code=404, detail="Project not found")
    except ExternalProviderError as e:
        logger.error(f"Provider failed for project {project_id}: {e}")
        raise HTTPException(status_code=502, detail="External service unavailable")
```

### Python (Service layer)

```python
# Services: business logic, clean error types
async def generate(self, project_id: str) -> list[CreativeBrief]:
    project = await self.project_repo.get(project_id)
    if not project:
        raise ProjectNotFoundError(project_id)
    # ... business logic
```

### Python (Repository layer)

```python
# Repositories: translate infrastructure errors to domain errors
async def get(self, project_id: str) -> Project | None:
    try:
        return await self.db.get(Project, project_id)
    except SQLAlchemyError as e:
        raise DatabaseError(f"Failed to fetch project {project_id}") from e
```

### TypeScript

```typescript
// API client: catch and surface errors
export async function fetchBriefs(projectId: string): Promise<Brief[]> {
  const res = await fetch(`/api/projects/${projectId}/briefs`);
  if (!res.ok) {
    throw new ApiError(res.status, await res.text());
  }
  return res.json();
}
```

### Principles

1. Never swallow errors. Every `except`/`catch` must re-raise, log, or surface.
2. Fail fast at boundaries — validate in routes/pages, not deep in services.
3. Use typed errors — `ProjectNotFoundError`, `ExternalProviderError`, not bare `Exception`.
4. Log context — include operation, entity ID, and original error.
5. Clean up on failure — roll back partial state, clear loading indicators.

---

## Provider Abstraction Pattern

All external services use Protocol-based interfaces:

```python
class LLMProvider(Protocol):
    async def generate(self, messages: list[dict], schema: dict | None = None) -> dict: ...

class TTSProvider(Protocol):
    async def synthesize(self, text: str, voice: str) -> bytes: ...

class MusicProvider(Protocol):
    async def generate(self, prompt: str, duration: int) -> bytes: ...
```

Concrete implementations live in `providers/<category>/`. Configuration selects which implementation is active. Services and Agents never reference concrete providers directly.

### Provider Lifecycle

Providers that hold resources (HTTP clients, connections) must implement an `aclose()` async method. FastAPI dependencies that yield providers must use `try/finally` to call `aclose()` after the request:

```python
async def get_llm_provider() -> AsyncGenerator:
    provider = _get_llm_provider()
    try:
        yield provider
    finally:
        await provider.aclose()
```

---

## Composition JSON Contract

The `RenderJob.composition` field is the contract between AI planning and video rendering. It fully describes a video as a layered timeline:

```json
{
  "duration": 15,
  "resolution": [1080, 1920],
  "fps": 30,
  "layers": [
    { "type": "video", "asset_id": "...", "start": 0, "end": 8 },
    { "type": "text", "content": "...", "start": 0, "end": 3 },
    { "type": "audio", "asset_id": "...", "start": 0, "end": 15 }
  ]
}
```

Schema changes to Composition JSON require a decision record in `docs/decisions/`.

---

## Serialization

- External data (JSON, DB): `snake_case` keys.
- Internal Python: `snake_case` attributes.
- Internal TypeScript: `camelCase` properties.
- Pydantic handles Python ↔ JSON translation. TypeScript API client transforms at the boundary.
- Enums stored as string names, never numeric indices.
- Dates as ISO 8601 UTC strings. Local time only at display layer.

---

## Code Smells

| Smell | Fix |
|-------|-----|
| File exceeds 300 lines | Split into focused modules |
| Empty except/catch block | Add logging at minimum |
| Hardcoded URLs, secrets, magic numbers | Extract to env vars or constants |
| Raw DB queries in routes | Move to repository |
| Provider SDK calls outside providers/ | Wrap in provider interface |
| Missing mounted/alive check after await in React | Add cleanup or abort controller |

---

## Formatting and Linting

- **Python:** `ruff check` (linting), `ruff format` (formatting). Zero warnings policy.
- **TypeScript:** `eslint` (linting), `prettier` (formatting). Zero warnings policy.
- Line length: 88 (Python/ruff), default (TypeScript/prettier).
- Trailing commas: yes (both languages).
