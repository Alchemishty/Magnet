"""Service layer for RenderJob operations."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.errors import NotFoundError
from app.models.job import RenderJob
from app.repositories.brief_repository import BriefRepository
from app.repositories.job_repository import RenderJobRepository
from app.schemas.job import JobCreate, JobUpdate


class JobService:
    """Orchestrates RenderJob business logic."""

    def __init__(self, session: Session):
        self._job_repo = RenderJobRepository(session)
        self._brief_repo = BriefRepository(session)

    def create_job(self, data: JobCreate) -> RenderJob:
        """Create a render job after verifying the brief exists."""
        brief = self._brief_repo.get_by_id(data.brief_id)
        if brief is None:
            raise NotFoundError("CreativeBrief", data.brief_id)
        return self._job_repo.create_from_schema(data)

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
