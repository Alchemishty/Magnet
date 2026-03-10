import pytest

from app.repositories.brief_repository import BriefRepository
from app.repositories.job_repository import RenderJobRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.user_repository import UserRepository
from app.schemas.brief import BriefCreate
from app.schemas.job import JobCreate, JobUpdate
from app.schemas.project import ProjectCreate
from app.schemas.user import UserCreate


@pytest.mark.integration
class TestRenderJobRepositoryIntegration:
    def _create_chain(self, db_session):
        """Create user -> project -> brief FK chain."""
        user = UserRepository(db_session).create_from_schema(
            UserCreate(
                email=f"job-user-{id(db_session)}@example.com",
                name="Job User",
            )
        )
        project = ProjectRepository(db_session).create_from_schema(
            ProjectCreate(name="Job Game", user_id=user.id)
        )
        brief = BriefRepository(db_session).create_from_schema(
            BriefCreate(project_id=project.id)
        )
        return user, project, brief

    def test_create_and_get_by_id(self, db_session):
        _, _, brief = self._create_chain(db_session)
        repo = RenderJobRepository(db_session)

        job = repo.create_from_schema(JobCreate(brief_id=brief.id))

        assert job.id is not None
        assert job.status == "queued"
        fetched = repo.get_by_id(job.id)
        assert fetched is not None

    def test_list_by_brief_all(self, db_session):
        _, _, brief = self._create_chain(db_session)
        repo = RenderJobRepository(db_session)

        repo.create_from_schema(JobCreate(brief_id=brief.id))
        repo.create_from_schema(JobCreate(brief_id=brief.id, status="rendering"))

        jobs = repo.list_by_brief(brief.id)

        assert len(jobs) == 2

    def test_list_by_brief_filtered_by_status(self, db_session):
        _, _, brief = self._create_chain(db_session)
        repo = RenderJobRepository(db_session)

        repo.create_from_schema(JobCreate(brief_id=brief.id))
        repo.create_from_schema(JobCreate(brief_id=brief.id, status="rendering"))

        jobs = repo.list_by_brief(brief.id, status="rendering")

        assert len(jobs) == 1
        assert jobs[0].status == "rendering"

    def test_update_to_done(self, db_session):
        _, _, brief = self._create_chain(db_session)
        repo = RenderJobRepository(db_session)

        job = repo.create_from_schema(JobCreate(brief_id=brief.id))

        updated = repo.update_from_schema(
            job.id,
            JobUpdate(
                status="done",
                output_s3_key="renders/output.mp4",
                render_duration_ms=5000,
            ),
        )

        assert updated is not None
        assert updated.status == "done"
        assert updated.output_s3_key == "renders/output.mp4"
        assert updated.render_duration_ms == 5000

    def test_update_to_failed(self, db_session):
        _, _, brief = self._create_chain(db_session)
        repo = RenderJobRepository(db_session)

        job = repo.create_from_schema(JobCreate(brief_id=brief.id))

        updated = repo.update_from_schema(
            job.id,
            JobUpdate(status="failed", error_message="Render timeout"),
        )

        assert updated is not None
        assert updated.status == "failed"
        assert updated.error_message == "Render timeout"

    def test_delete_job(self, db_session):
        _, _, brief = self._create_chain(db_session)
        repo = RenderJobRepository(db_session)

        job = repo.create_from_schema(JobCreate(brief_id=brief.id))

        result = repo.delete(job.id)

        assert result is True
        assert repo.get_by_id(job.id) is None
