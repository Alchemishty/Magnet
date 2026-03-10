"""Unit tests for the render task."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.models.job import RenderJob


class TestProcessRenderJob:
    @patch("app.tasks.render.SessionLocal")
    @patch("app.tasks.render.RenderJobRepository")
    def test_happy_path_updates_status_to_done(
        self, mock_repo_cls, mock_session_cls
    ):
        job_id = uuid4()
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_repo = mock_repo_cls.return_value
        mock_job = MagicMock(spec=RenderJob)
        mock_repo.get_by_id.return_value = mock_job

        from app.tasks.render import process_render_job

        process_render_job(str(job_id))

        mock_repo.get_by_id.assert_called_once_with(job_id)
        update_calls = mock_repo.update.call_args_list
        statuses = [call[0][1]["status"] for call in update_calls]
        assert statuses == ["rendering", "done"]

    @patch("app.tasks.render.SessionLocal")
    @patch("app.tasks.render.RenderJobRepository")
    def test_sets_failed_status_on_error(self, mock_repo_cls, mock_session_cls):
        job_id = uuid4()
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_repo = mock_repo_cls.return_value
        mock_job = MagicMock(spec=RenderJob)
        mock_repo.get_by_id.return_value = mock_job
        mock_repo.update.side_effect = [
            None,  # rendering update succeeds
            RuntimeError("simulated failure"),  # done update fails
            None,  # failed status update succeeds
        ]

        from app.tasks.render import process_render_job

        with pytest.raises(RuntimeError):
            process_render_job(str(job_id))

        failed_call = mock_repo.update.call_args_list[2]
        assert failed_call[0][1]["status"] == "failed"
        assert "simulated failure" in failed_call[0][1]["error_message"]

    @patch("app.tasks.render.SessionLocal")
    @patch("app.tasks.render.RenderJobRepository")
    def test_raises_when_job_not_found(self, mock_repo_cls, mock_session_cls):
        job_id = uuid4()
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_repo = mock_repo_cls.return_value
        mock_repo.get_by_id.return_value = None

        from app.tasks.render import process_render_job

        with pytest.raises(ValueError, match="not found"):
            process_render_job(str(job_id))

    @patch("app.tasks.render.SessionLocal")
    @patch("app.tasks.render.RenderJobRepository")
    def test_always_closes_db_session(self, mock_repo_cls, mock_session_cls):
        job_id = uuid4()
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_repo = mock_repo_cls.return_value
        mock_repo.get_by_id.return_value = MagicMock(spec=RenderJob)

        from app.tasks.render import process_render_job

        process_render_job(str(job_id))

        mock_session.close.assert_called_once()

    @patch("app.tasks.render.SessionLocal")
    @patch("app.tasks.render.RenderJobRepository")
    def test_closes_session_even_on_error(self, mock_repo_cls, mock_session_cls):
        job_id = uuid4()
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_repo = mock_repo_cls.return_value
        mock_repo.get_by_id.return_value = None

        from app.tasks.render import process_render_job

        with pytest.raises(ValueError):
            process_render_job(str(job_id))

        mock_session.close.assert_called_once()
