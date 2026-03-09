"""Routes for creative brief management and concept generation."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.errors import DatabaseError, NotFoundError, ValidationError
from app.routes.dependencies import get_brief_service
from app.schemas.brief import BriefRead, BriefUpdate
from app.services.brief_service import BriefService

router = APIRouter(tags=["briefs"])


@router.get(
    "/api/projects/{project_id}/briefs",
    response_model=list[BriefRead],
)
def list_briefs(
    project_id: UUID,
    status: str | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    service: BriefService = Depends(get_brief_service),
) -> list[BriefRead]:
    """List briefs for a project, optionally filtered by status."""
    try:
        briefs = service.list_briefs(project_id, status, offset, limit)
        return [BriefRead.model_validate(b) for b in briefs]
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=e.message)


@router.post(
    "/api/projects/{project_id}/concepts",
    status_code=501,
    responses={501: {"description": "LLM provider not yet configured"}},
)
async def generate_concepts(project_id: UUID) -> dict:
    """Trigger concept generation for a project.

    Returns 501 until a real LLM provider is wired in.
    """
    raise HTTPException(
        status_code=501,
        detail="LLM provider not configured",
    )


@router.get(
    "/api/briefs/{brief_id}",
    response_model=BriefRead,
)
def get_brief(
    brief_id: UUID,
    service: BriefService = Depends(get_brief_service),
) -> BriefRead:
    """Fetch a single brief by ID."""
    try:
        brief = service.get_brief(brief_id)
        return BriefRead.model_validate(brief)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=e.message)


@router.patch(
    "/api/briefs/{brief_id}",
    response_model=BriefRead,
)
def update_brief(
    brief_id: UUID,
    data: BriefUpdate,
    service: BriefService = Depends(get_brief_service),
) -> BriefRead:
    """Update a brief."""
    try:
        brief = service.update_brief(brief_id, data)
        return BriefRead.model_validate(brief)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=e.message)


@router.delete(
    "/api/briefs/{brief_id}",
    status_code=204,
)
def delete_brief(
    brief_id: UUID,
    service: BriefService = Depends(get_brief_service),
) -> None:
    """Delete a brief."""
    try:
        service.delete_brief(brief_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=e.message)
