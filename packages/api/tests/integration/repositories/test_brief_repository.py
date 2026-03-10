import pytest

from app.repositories.brief_repository import BriefRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.schemas.brief import BriefCreate, BriefUpdate
from app.schemas.project import ProjectCreate
from app.schemas.user import UserCreate


@pytest.mark.integration
class TestBriefRepositoryIntegration:
    def _create_user_and_project(self, db_session):
        user_repo = UserRepository(db_session)
        user = user_repo.create_from_schema(
            UserCreate(
                email=f"brief-user-{id(db_session)}@example.com",
                name="Brief User",
            )
        )
        project_repo = ProjectRepository(db_session)
        project = project_repo.create_from_schema(
            ProjectCreate(name="Brief Game", user_id=user.id)
        )
        return user, project

    def test_create_and_get_by_id(self, db_session):
        _, project = self._create_user_and_project(db_session)
        repo = BriefRepository(db_session)

        brief = repo.create_from_schema(
            BriefCreate(
                project_id=project.id,
                hook_type="fail_challenge",
                narrative_angle="Can you beat this?",
            )
        )

        assert brief.id is not None
        fetched = repo.get_by_id(brief.id)
        assert fetched is not None
        assert fetched.hook_type == "fail_challenge"

    def test_list_by_project_all(self, db_session):
        _, project = self._create_user_and_project(db_session)
        repo = BriefRepository(db_session)

        repo.create_from_schema(BriefCreate(project_id=project.id, status="draft"))
        repo.create_from_schema(BriefCreate(project_id=project.id, status="approved"))

        briefs = repo.list_by_project(project.id)

        assert len(briefs) == 2

    def test_list_by_project_filtered_by_status(self, db_session):
        _, project = self._create_user_and_project(db_session)
        repo = BriefRepository(db_session)

        repo.create_from_schema(BriefCreate(project_id=project.id, status="draft"))
        repo.create_from_schema(BriefCreate(project_id=project.id, status="approved"))

        briefs = repo.list_by_project(project.id, status="approved")

        assert len(briefs) == 1
        assert briefs[0].status == "approved"

    def test_update_status_draft_to_approved(self, db_session):
        _, project = self._create_user_and_project(db_session)
        repo = BriefRepository(db_session)

        brief = repo.create_from_schema(
            BriefCreate(project_id=project.id, status="draft")
        )

        updated = repo.update_from_schema(brief.id, BriefUpdate(status="approved"))

        assert updated is not None
        assert updated.status == "approved"

    def test_delete_brief(self, db_session):
        _, project = self._create_user_and_project(db_session)
        repo = BriefRepository(db_session)

        brief = repo.create_from_schema(BriefCreate(project_id=project.id))

        result = repo.delete(brief.id)

        assert result is True
        assert repo.get_by_id(brief.id) is None
