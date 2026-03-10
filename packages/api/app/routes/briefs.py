"""Routes for creative brief management and concept generation."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.agents.concept_agent import ConceptAgent, ConceptAgentError
from app.errors import (
    DatabaseError,
    ExternalProviderError,
    NotFoundError,
    ValidationError,
)
from app.routes.dependencies import (
    get_brief_service,
    get_concept_agent,
    get_concept_service,
)
from app.schemas.brief import BriefRead, BriefStatus, BriefUpdate
from app.services.brief_service import BriefService
from app.services.concept_service import ConceptService

router = APIRouter(tags=["briefs"])


@router.get(
    "/api/projects/{project_id}/briefs",
    response_model=list[BriefRead],
)
def list_briefs(
    project_id: UUID,
    status: BriefStatus | None = Query(default=None),
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
    response_model=list[BriefRead],
    status_code=201,
)
async def generate_concepts(
    project_id: UUID,
    service: ConceptService = Depends(get_concept_service),
    agent: ConceptAgent = Depends(get_concept_agent),
) -> list[BriefRead]:
    """Trigger concept generation for a project."""
    try:
        briefs = await service.generate_concepts(
            project_id, agent.generate_briefs
        )
        return [BriefRead.model_validate(b) for b in briefs]
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=e.message)
    except ExternalProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except ConceptAgentError as e:
        raise HTTPException(status_code=502, detail=str(e))


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
