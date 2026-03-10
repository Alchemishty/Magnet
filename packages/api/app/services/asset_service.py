"""Service layer for Asset operations."""

import logging
from uuid import UUID

from sqlalchemy.orm import Session

from app.errors import NotFoundError, StorageError
from app.models.asset import Asset
from app.repositories.asset_repository import AssetRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.s3_client import S3Client
from app.schemas.asset import AssetCreate

logger = logging.getLogger(__name__)


class AssetService:
    """Orchestrates asset business logic."""

    def __init__(self, session: Session, s3_client: S3Client | None = None):
        self._asset_repo = AssetRepository(session)
        self._project_repo = ProjectRepository(session)
        self._s3 = s3_client

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
        if self._s3:
            asset = self._asset_repo.get_by_id(asset_id)
            if asset is None:
                raise NotFoundError("Asset", asset_id)
            s3_key = asset.s3_key

        deleted = self._asset_repo.delete(asset_id)
        if not deleted:
            raise NotFoundError("Asset", asset_id)

        if self._s3:
            try:
                self._s3.delete_object(s3_key)
            except StorageError:
                logger.warning("Failed to delete S3 object %s", s3_key)
