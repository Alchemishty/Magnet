from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.errors import DatabaseError
from app.models.job import RenderJob
from app.repositories.base import BaseRepository
from app.schemas.job import JobCreate, JobUpdate


class RenderJobRepository(BaseRepository[RenderJob]):
    """Repository for RenderJob entity operations."""

    def __init__(self, session: Session):
        super().__init__(session, RenderJob)

    def list_by_brief(
        self,
        brief_id: UUID,
        status: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[RenderJob]:
        """List render jobs for a brief, optionally filtered by status."""
        try:
            query = self._session.query(RenderJob).filter(
                RenderJob.brief_id == brief_id
            )
            if status is not None:
                query = query.filter(RenderJob.status == status)
            return query.offset(offset).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(
                f"Failed to list render jobs for brief {brief_id}"
            ) from e

    def create_from_schema(self, schema: JobCreate) -> RenderJob:
        """Create a render job from a JobCreate schema."""
        data = schema.model_dump()
        # Convert Composition pydantic model to dict for JSONB storage
        if data.get("composition") is not None:
            data["composition"] = schema.composition.model_dump()
        return self.create(data)

    def update_from_schema(
        self, entity_id: UUID, schema: JobUpdate
    ) -> RenderJob | None:
        """Update a render job from a JobUpdate schema."""
        data = schema.model_dump(exclude_unset=True)
        # Convert Composition pydantic model to dict for JSONB storage
        if "composition" in data and data["composition"] is not None:
            data["composition"] = schema.composition.model_dump()
        return self.update(entity_id, data)
