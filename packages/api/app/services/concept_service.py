"""Service for generating creative concept briefs from a game profile."""

from collections.abc import Awaitable, Callable
from uuid import UUID

from sqlalchemy.orm import Session

from app.errors import NotFoundError, ValidationError
from app.models.brief import CreativeBrief
from app.repositories.brief_repository import BriefRepository
from app.repositories.game_profile_repository import GameProfileRepository
from app.schemas.brief import BriefCreate
from app.schemas.project import GameProfileRead


class ConceptService:
    """Orchestrates concept generation: fetch profile, generate, persist."""

    def __init__(self, session: Session):
        self._profile_repo = GameProfileRepository(session)
        self._brief_repo = BriefRepository(session)

    async def generate_concepts(
        self,
        project_id: UUID,
        generate_briefs_fn: Callable[[GameProfileRead], Awaitable[list[BriefCreate]]],
    ) -> list[CreativeBrief]:
        """Generate creative briefs for a project.

        Args:
            project_id: The project to generate briefs for.
            generate_briefs_fn: An async callable that accepts a
                GameProfileRead and returns a list of BriefCreate schemas.
                Typically ``ConceptAgent.generate_briefs``, injected by
                the route layer to keep import direction clean.

        Returns:
            A list of persisted CreativeBrief ORM instances.

        Raises:
            NotFoundError: If the project has no GameProfile.
            ValidationError: If the GameProfile is incomplete.
        """
        game_profile = self._profile_repo.get_by_project_id(project_id)
        if game_profile is None:
            raise NotFoundError("GameProfile", project_id)

        if not game_profile.genre or not game_profile.target_audience:
            raise ValidationError(
                "GameProfile requires at least genre and target_audience "
                "before generating concepts"
            )

        profile_schema = GameProfileRead.model_validate(game_profile)
        brief_schemas = await generate_briefs_fn(profile_schema)

        return [self._brief_repo.create_from_schema(s) for s in brief_schemas]
