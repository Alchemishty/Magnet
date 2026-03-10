from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.errors import DatabaseError
from app.models.asset import Asset
from app.repositories.base import BaseRepository
from app.schemas.asset import AssetCreate, AssetUpdate


class AssetRepository(BaseRepository[Asset]):
    """Repository for Asset entity operations."""

    def __init__(self, session: Session):
        super().__init__(session, Asset)

    def list_by_project(
        self,
        project_id: UUID,
        asset_type: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Asset]:
        """List assets for a project, optionally filtered by asset_type."""
        try:
            query = self._session.query(Asset).filter(Asset.project_id == project_id)
            if asset_type is not None:
                query = query.filter(Asset.asset_type == asset_type)
            return query.offset(offset).limit(limit).all()
        except SQLAlchemyError as e:
            raise DatabaseError(
                f"Failed to list assets for project {project_id}"
            ) from e

    def create_from_schema(self, schema: AssetCreate) -> Asset:
        """Create an asset from an AssetCreate schema."""
        return self.create(schema.model_dump())

    def update_from_schema(self, entity_id: UUID, schema: AssetUpdate) -> Asset | None:
        """Update an asset from an AssetUpdate schema."""
        return self.update(entity_id, schema.model_dump(exclude_unset=True))
