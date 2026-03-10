from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.errors import DatabaseError
from app.models.project import Project
from app.repositories.base import BaseRepository
from app.schemas.project import ProjectCreate, ProjectUpdate


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project entity operations."""

    def __init__(self, session: Session):
        super().__init__(session, Project)

    def list_by_user(
        self,
        user_id: UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Project]:
        """List projects belonging to a specific user."""
        try:
            return (
                self._session.query(Project)
                .filter(Project.user_id == user_id)
                .offset(offset)
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(f"Failed to list projects for user {user_id}") from e

    def create_from_schema(self, schema: ProjectCreate) -> Project:
        """Create a project from a ProjectCreate schema."""
        return self.create(schema.model_dump())

    def update_from_schema(
        self, entity_id: UUID, schema: ProjectUpdate
    ) -> Project | None:
        """Update a project from a ProjectUpdate schema."""
        return self.update(entity_id, schema.model_dump(exclude_unset=True))
