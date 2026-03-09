from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.errors import DatabaseError
from app.models.brief import CreativeBrief
from app.repositories.base import BaseRepository
from app.schemas.brief import BriefCreate, BriefUpdate


class BriefRepository(BaseRepository[CreativeBrief]):
    """Repository for CreativeBrief entity operations."""

    def __init__(self, session: Session):
        super().__init__(session, CreativeBrief)

    def list_by_project(
        self,
        project_id: UUID,
        status: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[CreativeBrief]:
        """List briefs for a project, optionally filtered by status."""
        try:
            query = self._session.query(CreativeBrief).filter(
                CreativeBrief.project_id == project_id
            )
            if status is not None:
                query = query.filter(CreativeBrief.status == status)
            return query.offset(offset).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(
                f"Failed to list briefs for project {project_id}"
            ) from e

    def create_from_schema(self, schema: BriefCreate) -> CreativeBrief:
        """Create a brief from a BriefCreate schema."""
        return self.create(schema.model_dump())

    def update_from_schema(
        self, entity_id: UUID, schema: BriefUpdate
    ) -> CreativeBrief | None:
        """Update a brief from a BriefUpdate schema."""
        return self.update(entity_id, schema.model_dump(exclude_unset=True))
