# Error Handling

## Python (API layer)

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

## Python (Service layer)

```python
# Services: business logic, clean error types
async def generate(self, project_id: str) -> list[CreativeBrief]:
    project = await self.project_repo.get(project_id)
    if not project:
        raise ProjectNotFoundError(project_id)
    # ... business logic
```

## Python (Repository layer)

```python
# Repositories: translate infrastructure errors to domain errors
async def get(self, project_id: str) -> Project | None:
    try:
        return await self.db.get(Project, project_id)
    except SQLAlchemyError as e:
        raise DatabaseError(f"Failed to fetch project {project_id}") from e
```

## TypeScript

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

## Principles

1. Never swallow errors. Every `except`/`catch` must re-raise, log, or surface.
2. Fail fast at boundaries — validate in routes/pages, not deep in services.
3. Use typed errors — `ProjectNotFoundError`, `ExternalProviderError`, not bare `Exception`.
4. Log context — include operation, entity ID, and original error.
5. Clean up on failure — roll back partial state, clear loading indicators.
