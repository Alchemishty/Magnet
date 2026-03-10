"""Unit tests for JobService."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.errors import NotFoundError
from app.models.job import RenderJob
from app.schemas.job import JobCreate, JobUpdate
from app.services.job_service import JobService


@pytest.fixture
def session():
    return MagicMock()


@pytest.fixture
def service(session):
    return JobService(session)


# ── create_job ───────────────────────────────────────────────────────


class TestCreateJob:
    @patch("app.services.job_service.BriefRepository")
    @patch("app.services.job_service.RenderJobRepository")
    def test_creates_job_when_brief_exists(
        self, mock_job_repo, mock_brief_repo, session
    ):
        brief_id = uuid4()
        mock_brief_repo = mock_brief_repo.return_value
        mock_brief_repo.get_by_id.return_value = MagicMock()

        mock_job_repo = mock_job_repo.return_value
        expected_job = MagicMock(spec=RenderJob)
        mock_job_repo.create_from_schema.return_value = expected_job

        data = JobCreate(brief_id=brief_id)
        svc = JobService(session)
        result = svc.create_job(data)

        mock_brief_repo.get_by_id.assert_called_once_with(brief_id)
        mock_job_repo.create_from_schema.assert_called_once_with(data)
        assert result is expected_job

    @patch("app.services.job_service.BriefRepository")
    @patch("app.services.job_service.RenderJobRepository")
    def test_raises_not_found_when_brief_missing(
        self, mock_job_repo, mock_brief_repo, session
    ):
        brief_id = uuid4()
        mock_brief_repo = mock_brief_repo.return_value
        mock_brief_repo.get_by_id.return_value = None

        data = JobCreate(brief_id=brief_id)
        svc = JobService(session)

        with pytest.raises(NotFoundError) as exc_info:
            svc.create_job(data)

        assert exc_info.value.entity_name == "CreativeBrief"
        assert exc_info.value.entity_id == brief_id

    @patch("app.services.job_service.BriefRepository")
    @patch("app.services.job_service.RenderJobRepository")
    def test_calls_dispatch_task_with_job_id(
        self, mock_job_repo, mock_brief_repo, session
    ):
        brief_id = uuid4()
        mock_brief_repo.return_value.get_by_id.return_value = MagicMock()
        expected_job = MagicMock(spec=RenderJob)
        expected_job.id = uuid4()
        mock_job_repo.return_value.create_from_schema.return_value = expected_job
        dispatcher = MagicMock()

        data = JobCreate(brief_id=brief_id)
        svc = JobService(session)
        svc.create_job(data, dispatch_task=dispatcher)

        dispatcher.assert_called_once_with(str(expected_job.id))

    @patch("app.services.job_service.BriefRepository")
    @patch("app.services.job_service.RenderJobRepository")
    def test_no_dispatch_when_none(
        self, mock_job_repo, mock_brief_repo, session
    ):
        brief_id = uuid4()
        mock_brief_repo.return_value.get_by_id.return_value = MagicMock()
        expected_job = MagicMock(spec=RenderJob)
        mock_job_repo.return_value.create_from_schema.return_value = expected_job

        data = JobCreate(brief_id=brief_id)
        svc = JobService(session)
        result = svc.create_job(data)

        assert result is expected_job

    @patch("app.services.job_service.BriefRepository")
    @patch("app.services.job_service.RenderJobRepository")
    def test_job_created_even_if_dispatch_fails(
        self, mock_job_repo, mock_brief_repo, session
    ):
        brief_id = uuid4()
        mock_brief_repo.return_value.get_by_id.return_value = MagicMock()
        expected_job = MagicMock(spec=RenderJob)
        expected_job.id = uuid4()
        mock_job_repo.return_value.create_from_schema.return_value = expected_job
        dispatcher = MagicMock(side_effect=RuntimeError("queue down"))

        data = JobCreate(brief_id=brief_id)
        svc = JobService(session)
        result = svc.create_job(data, dispatch_task=dispatcher)

        assert result is expected_job


# ── list_jobs ────────────────────────────────────────────────────────


class TestListJobs:
    @patch("app.services.job_service.RenderJobRepository")
    def test_lists_jobs_delegates_to_repo(self, mock_job_repo, session):
        brief_id = uuid4()
        expected = [MagicMock(spec=RenderJob)]
        mock_repo = mock_job_repo.return_value
        mock_repo.list_by_brief.return_value = expected

        svc = JobService(session)
        result = svc.list_jobs(brief_id, status="queued", offset=10, limit=50)

        mock_repo.list_by_brief.assert_called_once_with(
            brief_id, status="queued", offset=10, limit=50
        )
        assert result is expected

    @patch("app.services.job_service.RenderJobRepository")
    def test_lists_jobs_uses_defaults(self, mock_job_repo, session):
        brief_id = uuid4()
        mock_repo = mock_job_repo.return_value
        mock_repo.list_by_brief.return_value = []

        svc = JobService(session)
        result = svc.list_jobs(brief_id)

        mock_repo.list_by_brief.assert_called_once_with(
            brief_id, status=None, offset=0, limit=100
        )
        assert result == []


# ── get_job ──────────────────────────────────────────────────────────


class TestGetJob:
    @patch("app.services.job_service.RenderJobRepository")
    def test_returns_job_when_found(self, mock_job_repo, session):
        job_id = uuid4()
        expected = MagicMock(spec=RenderJob)
        mock_repo = mock_job_repo.return_value
        mock_repo.get_by_id.return_value = expected

        svc = JobService(session)
        result = svc.get_job(job_id)

        mock_repo.get_by_id.assert_called_once_with(job_id)
        assert result is expected

    @patch("app.services.job_service.RenderJobRepository")
    def test_raises_not_found_when_missing(self, mock_job_repo, session):
        job_id = uuid4()
        mock_repo = mock_job_repo.return_value
        mock_repo.get_by_id.return_value = None

        svc = JobService(session)

        with pytest.raises(NotFoundError) as exc_info:
            svc.get_job(job_id)

        assert exc_info.value.entity_name == "RenderJob"
        assert exc_info.value.entity_id == job_id


# ── update_job ───────────────────────────────────────────────────────


class TestUpdateJob:
    @patch("app.services.job_service.RenderJobRepository")
    def test_updates_job_when_found(self, mock_job_repo, session):
        job_id = uuid4()
        expected = MagicMock(spec=RenderJob)
        mock_repo = mock_job_repo.return_value
        mock_repo.update_from_schema.return_value = expected

        data = JobUpdate(status="done")
        svc = JobService(session)
        result = svc.update_job(job_id, data)

        mock_repo.update_from_schema.assert_called_once_with(job_id, data)
        assert result is expected

    @patch("app.services.job_service.RenderJobRepository")
    def test_raises_not_found_when_missing(self, mock_job_repo, session):
        job_id = uuid4()
        mock_repo = mock_job_repo.return_value
        mock_repo.update_from_schema.return_value = None

        data = JobUpdate(status="failed")
        svc = JobService(session)

        with pytest.raises(NotFoundError) as exc_info:
            svc.update_job(job_id, data)

        assert exc_info.value.entity_name == "RenderJob"
        assert exc_info.value.entity_id == job_id
