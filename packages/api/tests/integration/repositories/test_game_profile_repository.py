import pytest

from app.repositories.game_profile_repository import GameProfileRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.schemas.project import (
    GameProfileCreate,
    GameProfileUpdate,
    ProjectCreate,
)
from app.schemas.user import UserCreate


@pytest.mark.integration
class TestGameProfileRepositoryIntegration:
    def _create_user_and_project(self, db_session):
        user_repo = UserRepository(db_session)
        user = user_repo.create_from_schema(
            UserCreate(
                email=f"gp-user-{id(db_session)}@example.com",
                name="GP User",
            )
        )
        project_repo = ProjectRepository(db_session)
        project = project_repo.create_from_schema(
            ProjectCreate(name="GP Game", user_id=user.id)
        )
        return user, project

    def test_create_and_get_by_project_id(self, db_session):
        _, project = self._create_user_and_project(db_session)
        repo = GameProfileRepository(db_session)

        profile = repo.create_from_schema(
            GameProfileCreate(
                project_id=project.id,
                genre="puzzle",
                target_audience="casual gamers",
            )
        )

        assert profile.id is not None
        fetched = repo.get_by_project_id(project.id)
        assert fetched is not None
        assert fetched.genre == "puzzle"

    def test_update_game_profile(self, db_session):
        _, project = self._create_user_and_project(db_session)
        repo = GameProfileRepository(db_session)

        profile = repo.create_from_schema(
            GameProfileCreate(
                project_id=project.id,
                genre="puzzle",
            )
        )

        updated = repo.update_from_schema(
            profile.id, GameProfileUpdate(genre="action")
        )

        assert updated is not None
        assert updated.genre == "action"

    def test_delete_game_profile(self, db_session):
        _, project = self._create_user_and_project(db_session)
        repo = GameProfileRepository(db_session)

        profile = repo.create_from_schema(
            GameProfileCreate(project_id=project.id, genre="rpg")
        )

        result = repo.delete(profile.id)

        assert result is True
        assert repo.get_by_id(profile.id) is None
