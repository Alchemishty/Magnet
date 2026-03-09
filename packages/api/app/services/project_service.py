"""Service layer for Project and GameProfile operations."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.errors import NotFoundError
from app.models.project import GameProfile, Project
from app.repositories.game_profile_repository import GameProfileRepository
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import (
    GameProfileCreate,
    GameProfileUpdate,
    ProjectCreate,
    ProjectUpdate,
)


class ProjectService:
    """Orchestrates project and game-profile business logic."""

    def __init__(self, session: Session):
        self._project_repo = ProjectRepository(session)
        self._profile_repo = GameProfileRepository(session)

    # ── projects ─────────────────────────────────────────────────

    def create_project(self, data: ProjectCreate) -> Project:
        """Create a new project."""
        return self._project_repo.create_from_schema(data)

    def get_project(self, project_id: UUID) -> Project:
        """Return a project or raise NotFoundError."""
        project = self._project_repo.get_by_id(project_id)
        if project is None:
            raise NotFoundError("Project", project_id)
        return project

    def list_projects(
        self,
        user_id: UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Project]:
        """List projects belonging to a user."""
        return self._project_repo.list_by_user(user_id, offset=offset, limit=limit)

    def update_project(self, project_id: UUID, data: ProjectUpdate) -> Project:
        """Update a project or raise NotFoundError."""
        project = self._project_repo.update_from_schema(project_id, data)
        if project is None:
            raise NotFoundError("Project", project_id)
        return project

    def delete_project(self, project_id: UUID) -> None:
        """Delete a project or raise NotFoundError."""
        deleted = self._project_repo.delete(project_id)
        if not deleted:
            raise NotFoundError("Project", project_id)

    # ── game profiles ────────────────────────────────────────────

    def create_game_profile(self, data: GameProfileCreate) -> GameProfile:
        """Create a game profile, verifying the parent project exists."""
        project = self._project_repo.get_by_id(data.project_id)
        if project is None:
            raise NotFoundError("Project", data.project_id)
        return self._profile_repo.create_from_schema(data)

    def get_game_profile(self, project_id: UUID) -> GameProfile:
        """Return the game profile for a project or raise NotFoundError."""
        profile = self._profile_repo.get_by_project_id(project_id)
        if profile is None:
            raise NotFoundError("GameProfile", project_id)
        return profile

    def update_game_profile(
        self, project_id: UUID, data: GameProfileUpdate
    ) -> GameProfile:
        """Update a game profile looked up by project_id, or raise NotFoundError."""
        profile = self._profile_repo.get_by_project_id(project_id)
        if profile is None:
            raise NotFoundError("GameProfile", project_id)
        updated = self._profile_repo.update_from_schema(profile.id, data)
        return updated
