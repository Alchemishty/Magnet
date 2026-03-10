"""Service layer for RenderJob operations."""

import logging
from collections.abc import Callable
from uuid import UUID

from sqlalchemy.orm import Session

from app.errors import NotFoundError
from app.models.job import RenderJob
from app.repositories.brief_repository import BriefRepository
from app.repositories.job_repository import RenderJobRepository
from app.schemas.job import JobCreate, JobUpdate

logger = logging.getLogger(__name__)


class JobService:
    """Orchestrates RenderJob business logic."""

    def __init__(self, session: Session):
        self._job_repo = RenderJobRepository(session)
        self._brief_repo = BriefRepository(session)

    def create_job(
        self,
        data: JobCreate,
        dispatch_task: Callable[[str], object] | None = None,
    ) -> RenderJob:
        """Create a render job after verifying the brief exists.

        If dispatch_task is provided, dispatches the job for async processing.
        Dispatch failures are logged but do not prevent job creation.
        """
        brief = self._brief_repo.get_by_id(data.brief_id)
        if brief is None:
            raise NotFoundError("CreativeBrief", data.brief_id)
        job = self._job_repo.create_from_schema(data)
        if dispatch_task is not None:
            try:
                dispatch_task(str(job.id))
            except Exception:
                logger.exception("Failed to dispatch task for job %s", job.id)
        return job

    def list_jobs(
        self,
        brief_id: UUID,
        status: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[RenderJob]:
        """List render jobs for a brief."""
        return self._job_repo.list_by_brief(
            brief_id, status=status, offset=offset, limit=limit
        )

    def get_job(self, job_id: UUID) -> RenderJob:
        """Fetch a single render job or raise NotFoundError."""
        job = self._job_repo.get_by_id(job_id)
        if job is None:
            raise NotFoundError("RenderJob", job_id)
        return job

    def update_job(self, job_id: UUID, data: JobUpdate) -> RenderJob:
        """Update a render job or raise NotFoundError."""
        job = self._job_repo.update_from_schema(job_id, data)
        if job is None:
            raise NotFoundError("RenderJob", job_id)
        return job
