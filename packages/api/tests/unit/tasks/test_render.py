"""Unit tests for the render task."""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.models.brief import CreativeBrief
from app.models.job import RenderJob


class TestProcessRenderJob:
    @patch("app.tasks.render._run_video_agent")
    @patch("app.tasks.render.BriefRepository")
    @patch("app.tasks.render.SessionLocal")
    @patch("app.tasks.render.RenderJobRepository")
    def test_happy_path_updates_status_to_done(
        self, mock_repo_cls, mock_session_cls, mock_brief_repo_cls,
        mock_run_agent,
    ):
        job_id = uuid4()
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_repo = mock_repo_cls.return_value
        mock_job = MagicMock(spec=RenderJob)
        mock_job.brief_id = uuid4()
        mock_repo.get_by_id.return_value = mock_job

        mock_brief = MagicMock(spec=CreativeBrief)
        mock_brief_repo_cls.return_value.get_by_id.return_value = mock_brief

        mock_composition = MagicMock()
        mock_composition.model_dump.return_value = {"duration": 15}
        mock_run_agent.return_value = ("renders/x/output.mp4", mock_composition)

        from app.tasks.render import process_render_job

        process_render_job(str(job_id))

        mock_repo.get_by_id.assert_called_once_with(job_id)
        update_calls = mock_repo.update.call_args_list
        assert update_calls[0][0][1]["status"] == "rendering"
        assert update_calls[1][0][1]["status"] == "done"
        assert update_calls[1][0][1]["output_s3_key"] == "renders/x/output.mp4"

    @patch("app.tasks.render._run_video_agent")
    @patch("app.tasks.render.BriefRepository")
    @patch("app.tasks.render.SessionLocal")
    @patch("app.tasks.render.RenderJobRepository")
    def test_sets_failed_status_on_agent_error(
        self, mock_repo_cls, mock_session_cls, mock_brief_repo_cls,
        mock_run_agent,
    ):
        job_id = uuid4()
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_repo = mock_repo_cls.return_value
        mock_job = MagicMock(spec=RenderJob)
        mock_job.brief_id = uuid4()
        mock_repo.get_by_id.return_value = mock_job

        mock_brief = MagicMock(spec=CreativeBrief)
        mock_brief_repo_cls.return_value.get_by_id.return_value = mock_brief

        mock_run_agent.side_effect = RuntimeError("agent exploded")

        from app.tasks.render import process_render_job

        with pytest.raises(RuntimeError):
            process_render_job(str(job_id))

        failed_call = mock_repo.update.call_args_list[-1]
        assert failed_call[0][1]["status"] == "failed"
        assert "agent exploded" in failed_call[0][1]["error_message"]

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

    @patch("app.tasks.render._run_video_agent")
    @patch("app.tasks.render.BriefRepository")
    @patch("app.tasks.render.SessionLocal")
    @patch("app.tasks.render.RenderJobRepository")
    def test_always_closes_db_session(
        self, mock_repo_cls, mock_session_cls, mock_brief_repo_cls,
        mock_run_agent,
    ):
        job_id = uuid4()
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_repo = mock_repo_cls.return_value
        mock_job = MagicMock(spec=RenderJob)
        mock_job.brief_id = uuid4()
        mock_repo.get_by_id.return_value = mock_job

        mock_brief_repo_cls.return_value.get_by_id.return_value = MagicMock()
        mock_run_agent.return_value = ("path", MagicMock(model_dump=lambda: {}))

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

    @patch("app.tasks.render._run_video_agent")
    @patch("app.tasks.render.BriefRepository")
    @patch("app.tasks.render.SessionLocal")
    @patch("app.tasks.render.RenderJobRepository")
    def test_raises_when_brief_not_found(
        self, mock_repo_cls, mock_session_cls, mock_brief_repo_cls,
        mock_run_agent,
    ):
        job_id = uuid4()
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_repo = mock_repo_cls.return_value
        mock_job = MagicMock(spec=RenderJob)
        mock_job.brief_id = uuid4()
        mock_repo.get_by_id.return_value = mock_job

        mock_brief_repo_cls.return_value.get_by_id.return_value = None

        from app.tasks.render import process_render_job

        with pytest.raises(ValueError, match="CreativeBrief"):
            process_render_job(str(job_id))
