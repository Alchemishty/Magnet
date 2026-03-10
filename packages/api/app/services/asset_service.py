"""Service layer for Asset operations."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.errors import NotFoundError
from app.models.asset import Asset
from app.repositories.asset_repository import AssetRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.asset import AssetCreate


class AssetService:
    """Orchestrates asset business logic."""

    def __init__(self, session: Session):
        self._asset_repo = AssetRepository(session)
        self._project_repo = ProjectRepository(session)

    def create_asset(self, data: AssetCreate) -> Asset:
        """Create a new asset after verifying the project exists."""
        project = self._project_repo.get_by_id(data.project_id)
        if project is None:
            raise NotFoundError("Project", data.project_id)
        return self._asset_repo.create_from_schema(data)

    def list_assets(
        self,
        project_id: UUID,
        asset_type: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Asset]:
        """List assets for a project with optional filtering."""
        return self._asset_repo.list_by_project(project_id, asset_type, offset, limit)

    def get_asset(self, asset_id: UUID) -> Asset:
        """Get a single asset by ID or raise NotFoundError."""
        asset = self._asset_repo.get_by_id(asset_id)
        if asset is None:
            raise NotFoundError("Asset", asset_id)
        return asset

    def delete_asset(self, asset_id: UUID) -> None:
        """Delete an asset by ID or raise NotFoundError."""
        deleted = self._asset_repo.delete(asset_id)
        if not deleted:
            raise NotFoundError("Asset", asset_id)
