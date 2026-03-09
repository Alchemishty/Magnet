import pytest

from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.schemas.user import UserCreate


@pytest.mark.integration
class TestProjectRepositoryIntegration:
    def test_create_and_get_by_id(self, db_session):
        user_repo = UserRepository(db_session)
        user = user_repo.create_from_schema(
            UserCreate(email="proj-user@example.com", name="Proj User")
        )

        repo = ProjectRepository(db_session)
        project = repo.create_from_schema(
            ProjectCreate(name="My Game", user_id=user.id)
        )

        assert project.id is not None
        fetched = repo.get_by_id(project.id)
        assert fetched is not None
        assert fetched.name == "My Game"

    def test_list_by_user(self, db_session):
        user_repo = UserRepository(db_session)
        user = user_repo.create_from_schema(
            UserCreate(email="list-proj@example.com", name="List User")
        )

        repo = ProjectRepository(db_session)
        repo.create_from_schema(
            ProjectCreate(name="Game A", user_id=user.id)
        )
        repo.create_from_schema(
            ProjectCreate(name="Game B", user_id=user.id)
        )

        projects = repo.list_by_user(user.id)

        assert len(projects) == 2

    def test_update_project(self, db_session):
        user_repo = UserRepository(db_session)
        user = user_repo.create_from_schema(
            UserCreate(email="upd-proj@example.com", name="Upd User")
        )

        repo = ProjectRepository(db_session)
        project = repo.create_from_schema(
            ProjectCreate(name="Before", user_id=user.id)
        )

        updated = repo.update_from_schema(
            project.id, ProjectUpdate(name="After")
        )

        assert updated is not None
        assert updated.name == "After"

    def test_delete_project(self, db_session):
        user_repo = UserRepository(db_session)
        user = user_repo.create_from_schema(
            UserCreate(email="del-proj@example.com", name="Del User")
        )

        repo = ProjectRepository(db_session)
        project = repo.create_from_schema(
            ProjectCreate(name="Delete Me", user_id=user.id)
        )

        result = repo.delete(project.id)

        assert result is True
        assert repo.get_by_id(project.id) is None
