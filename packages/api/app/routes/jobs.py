"""Routes for RenderJob operations."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.errors import DatabaseError, NotFoundError
from app.routes.dependencies import get_job_service
from app.schemas.job import (
    JobCreate,
    JobCreateBody,
    JobRead,
    JobStatus,
    JobUpdate,
)
from app.services.job_service import JobService

router = APIRouter(tags=["jobs"])


@router.post(
    "/api/briefs/{brief_id}/jobs",
    response_model=JobRead,
    status_code=201,
)
def create_job(
    brief_id: UUID,
    body: JobCreateBody,
    service: JobService = Depends(get_job_service),
) -> JobRead:
    """Create a render job for a brief."""
    data = JobCreate(brief_id=brief_id, **body.model_dump())
    try:
        job = service.create_job(data)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=e.message)
    return job


@router.get(
    "/api/briefs/{brief_id}/jobs",
    response_model=list[JobRead],
)
def list_jobs(
    brief_id: UUID,
    status: JobStatus | None = Query(default=None),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    service: JobService = Depends(get_job_service),
) -> list[JobRead]:
    """List render jobs for a brief."""
    try:
        jobs = service.list_jobs(
            brief_id, status=status, offset=offset, limit=limit
        )
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=e.message)
    return jobs


@router.get(
    "/api/jobs/{job_id}",
    response_model=JobRead,
)
def get_job(
    job_id: UUID,
    service: JobService = Depends(get_job_service),
) -> JobRead:
    """Fetch a single render job."""
    try:
        job = service.get_job(job_id)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=e.message)
    return job


@router.patch(
    "/api/jobs/{job_id}",
    response_model=JobRead,
)
def update_job(
    job_id: UUID,
    body: JobUpdate,
    service: JobService = Depends(get_job_service),
) -> JobRead:
    """Update a render job."""
    try:
        job = service.update_job(job_id, body)
    except NotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    except DatabaseError as e:
        raise HTTPException(status_code=500, detail=e.message)
    return job
