# Naming Conventions

## Python

| Thing | Convention | Example |
|-------|-----------|---------|
| Files | `snake_case.py` | `concept_agent.py`, `brief_service.py` |
| Classes | `PascalCase` | `CreativeBrief`, `ConceptAgent` |
| Functions / Methods | `snake_case` | `generate_concepts`, `get_brief_by_id` |
| Variables | `snake_case` | `render_job`, `total_duration` |
| Constants | `SCREAMING_SNAKE_CASE` | `MAX_RETRIES`, `DEFAULT_FPS` |
| Private | `_prefix` | `_build_filter_graph` |

## TypeScript

| Thing | Convention | Example |
|-------|-----------|---------|
| Files | `kebab-case.ts(x)` | `project-form.tsx`, `api-client.ts` |
| Types / Interfaces | `PascalCase` | `CreativeBrief`, `RenderJob` |
| Functions / Variables | `camelCase` | `fetchBriefs`, `projectId` |
| Constants | `SCREAMING_SNAKE_CASE` | `API_BASE_URL` |
| React components | `PascalCase` | `BriefCard`, `AssetUploader` |

## Shared

| Thing | Convention |
|-------|-----------|
| Database columns | `snake_case` — `created_at`, `asset_type` |
| JSON keys (API) | `snake_case` — `{ "hook_type": "...", "render_duration_ms": 0 }` |
| URL paths | `kebab-case` — `/api/projects/:id/creative-briefs` |
| Environment variables | `SCREAMING_SNAKE_CASE` — `DATABASE_URL`, `REDIS_URL` |
| Booleans | `is_`/`has_`/`can_` prefix — `is_approved`, `hasPermission` |
