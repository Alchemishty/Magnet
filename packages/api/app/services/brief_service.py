"""Service layer for CreativeBrief operations."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.errors import NotFoundError
from app.models.brief import CreativeBrief
from app.repositories.brief_repository import BriefRepository
from app.schemas.brief import BriefUpdate


class BriefService:
    """Encapsulates business logic for creative briefs."""

    def __init__(self, session: Session):
        self._repo = BriefRepository(session)

    def list_briefs(
        self,
        project_id: UUID,
        status: str | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[CreativeBrief]:
        """List briefs for a project, optionally filtered by status."""
        return self._repo.list_by_project(project_id, status, offset, limit)

    def get_brief(self, brief_id: UUID) -> CreativeBrief:
        """Fetch a brief by ID. Raises NotFoundError if missing."""
        brief = self._repo.get_by_id(brief_id)
        if brief is None:
            raise NotFoundError("CreativeBrief", brief_id)
        return brief

    def update_brief(
        self, brief_id: UUID, data: BriefUpdate
    ) -> CreativeBrief:
        """Update a brief. Raises NotFoundError if missing."""
        brief = self._repo.update_from_schema(brief_id, data)
        if brief is None:
            raise NotFoundError("CreativeBrief", brief_id)
        return brief

    def delete_brief(self, brief_id: UUID) -> None:
        """Delete a brief. Raises NotFoundError if missing."""
        deleted = self._repo.delete(brief_id)
        if not deleted:
            raise NotFoundError("CreativeBrief", brief_id)
