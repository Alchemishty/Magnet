from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.errors import DatabaseError
from app.models.project import GameProfile
from app.repositories.base import BaseRepository
from app.schemas.project import GameProfileCreate, GameProfileUpdate


class GameProfileRepository(BaseRepository[GameProfile]):
    """Repository for GameProfile entity operations."""

    def __init__(self, session: Session):
        super().__init__(session, GameProfile)

    def get_by_project_id(self, project_id: UUID) -> GameProfile | None:
        """Find a game profile by project ID (unique constraint)."""
        try:
            return (
                self._session.query(GameProfile)
                .filter(GameProfile.project_id == project_id)
                .first()
            )
        except SQLAlchemyError as e:
            raise DatabaseError(
                f"Failed to fetch game profile for project {project_id}"
            ) from e

    def create_from_schema(self, schema: GameProfileCreate) -> GameProfile:
        """Create a game profile from a GameProfileCreate schema."""
        return self.create(schema.model_dump())

    def update_from_schema(
        self, entity_id: UUID, schema: GameProfileUpdate
    ) -> GameProfile | None:
        """Update a game profile from a GameProfileUpdate schema."""
        return self.update(entity_id, schema.model_dump(exclude_unset=True))
