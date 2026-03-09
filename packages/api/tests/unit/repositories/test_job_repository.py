from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.models.job import RenderJob
from app.repositories.job_repository import RenderJobRepository
from app.schemas.job import JobCreate, JobUpdate


@pytest.fixture()
def mock_session():
    return MagicMock()


@pytest.fixture()
def repo(mock_session):
    return RenderJobRepository(mock_session)


class TestListByBrief:
    def test_returns_jobs_for_brief(self, repo, mock_session):
        jobs = [RenderJob(brief_id=uuid4())]
        query = MagicMock()
        mock_session.query.return_value = query
        query.filter.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = jobs

        result = repo.list_by_brief(uuid4())

        assert result == jobs

    def test_filters_by_status(self, repo, mock_session):
        query = MagicMock()
        mock_session.query.return_value = query
        query.filter.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = []

        repo.list_by_brief(uuid4(), status="done")

        # filter called twice: brief_id + status
        assert query.filter.call_count == 2

    def test_without_status_filter(self, repo, mock_session):
        query = MagicMock()
        mock_session.query.return_value = query
        query.filter.return_value = query
        query.offset.return_value = query
        query.limit.return_value = query
        query.all.return_value = []

        repo.list_by_brief(uuid4())

        assert query.filter.call_count == 1


class TestCreateFromSchema:
    def test_creates_job(self, repo, mock_session):
        schema = JobCreate(brief_id=uuid4())

        result = repo.create_from_schema(schema)

        assert isinstance(result, RenderJob)
        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()


class TestUpdateFromSchema:
    def test_updates_job_status(self, repo, mock_session):
        job = RenderJob(brief_id=uuid4())
        entity_id = uuid4()
        mock_session.get.return_value = job
        schema = JobUpdate(status="done")

        result = repo.update_from_schema(entity_id, schema)

        assert result is job
        assert job.status == "done"

    def test_updates_job_with_error(self, repo, mock_session):
        job = RenderJob(brief_id=uuid4())
        entity_id = uuid4()
        mock_session.get.return_value = job
        schema = JobUpdate(status="failed", error_message="Render timeout")

        result = repo.update_from_schema(entity_id, schema)

        assert result is job
        assert job.status == "failed"
        assert job.error_message == "Render timeout"
