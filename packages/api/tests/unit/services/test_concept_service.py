from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.errors import NotFoundError, ValidationError
from app.models.brief import CreativeBrief
from app.models.project import GameProfile
from app.schemas.brief import BriefCreate
from app.schemas.project import GameProfileRead
from app.services.concept_service import ConceptService


@pytest.fixture()
def mock_session():
    return MagicMock()


@pytest.fixture()
def service(mock_session):
    return ConceptService(mock_session)


@pytest.fixture()
def project_id():
    return uuid4()


@pytest.fixture()
def game_profile(project_id):
    """Create a GameProfile ORM instance with realistic data."""
    return GameProfile(
        id=uuid4(),
        project_id=project_id,
        genre="puzzle",
        target_audience="casual gamers",
        core_mechanics=["match-3"],
        art_style="cartoon",
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture()
def brief_schemas(project_id):
    return [
        BriefCreate(
            project_id=project_id,
            hook_type="fail_challenge",
            narrative_angle="frustration to triumph",
            target_emotion="excitement",
        ),
        BriefCreate(
            project_id=project_id,
            hook_type="satisfying_solve",
            narrative_angle="oddly satisfying",
            target_emotion="satisfaction",
        ),
    ]


@pytest.fixture()
def generate_briefs_fn(brief_schemas):
    fn = AsyncMock(return_value=brief_schemas)
    return fn


class TestGenerateConceptsHappyPath:
    @pytest.mark.asyncio
    async def test_returns_persisted_briefs(
        self,
        service,
        mock_session,
        project_id,
        game_profile,
        brief_schemas,
        generate_briefs_fn,
    ):
        """Happy path: fetches profile, calls generator, persists results."""
        with (
            patch.object(
                service._profile_repo,
                "get_by_project_id",
                return_value=game_profile,
            ),
            patch.object(
                service._brief_repo,
                "create_from_schema",
                side_effect=lambda s: CreativeBrief(**s.model_dump()),
            ),
        ):
            result = await service.generate_concepts(
                project_id,
                generate_briefs_fn,
            )

        # The generate fn was called with a GameProfileRead schema
        generate_briefs_fn.assert_awaited_once()
        call_arg = generate_briefs_fn.call_args[0][0]
        assert isinstance(call_arg, GameProfileRead)
        assert call_arg.project_id == project_id

        # Returns a list of CreativeBrief ORM objects
        assert len(result) == len(brief_schemas)
        for brief in result:
            assert isinstance(brief, CreativeBrief)

    @pytest.mark.asyncio
    async def test_persists_each_brief(
        self,
        service,
        mock_session,
        project_id,
        game_profile,
        brief_schemas,
        generate_briefs_fn,
    ):
        """Each generated BriefCreate is persisted via the repo."""
        with (
            patch.object(
                service._profile_repo,
                "get_by_project_id",
                return_value=game_profile,
            ),
            patch.object(
                service._brief_repo,
                "create_from_schema",
                side_effect=lambda s: CreativeBrief(**s.model_dump()),
            ) as mock_create,
        ):
            await service.generate_concepts(
                project_id,
                generate_briefs_fn,
            )

        assert mock_create.call_count == len(brief_schemas)
        for call, schema in zip(mock_create.call_args_list, brief_schemas):
            assert call[0][0] == schema


class TestGenerateConceptsProfileNotFound:
    @pytest.mark.asyncio
    async def test_raises_not_found_when_no_profile(
        self,
        service,
        project_id,
        generate_briefs_fn,
    ):
        """Raises NotFoundError when GameProfile doesn't exist."""
        with patch.object(
            service._profile_repo,
            "get_by_project_id",
            return_value=None,
        ):
            with pytest.raises(NotFoundError) as exc_info:
                await service.generate_concepts(
                    project_id,
                    generate_briefs_fn,
                )

        assert exc_info.value.entity_name == "GameProfile"
        assert exc_info.value.entity_id == project_id
        generate_briefs_fn.assert_not_awaited()


class TestGenerateConceptsValidationError:
    @pytest.mark.asyncio
    async def test_raises_validation_when_profile_incomplete(
        self,
        service,
        project_id,
        generate_briefs_fn,
    ):
        """Raises ValidationError when profile has no genre."""
        incomplete_profile = GameProfile(
            id=uuid4(),
            project_id=project_id,
            genre=None,
            target_audience=None,
            created_at=datetime.now(timezone.utc),
        )
        with patch.object(
            service._profile_repo,
            "get_by_project_id",
            return_value=incomplete_profile,
        ):
            with pytest.raises(ValidationError) as exc_info:
                await service.generate_concepts(
                    project_id,
                    generate_briefs_fn,
                )

        assert "GameProfile" in exc_info.value.message
        generate_briefs_fn.assert_not_awaited()
