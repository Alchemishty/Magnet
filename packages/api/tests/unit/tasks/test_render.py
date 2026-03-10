"""Unit tests for the render task."""

from unittest.mock import AsyncMock, MagicMock, call, patch
from uuid import uuid4

import pytest

from app.models.brief import CreativeBrief
from app.models.job import RenderJob


def _make_job_and_session(job_id=None, brief_id=None):
    """Helper to set up common mock objects for render task tests."""
    job_id = job_id or uuid4()
    brief_id = brief_id or uuid4()
    mock_session = MagicMock()
    mock_repo = MagicMock()
    mock_job = MagicMock(spec=RenderJob)
    mock_job.brief_id = brief_id
    mock_repo.get_by_id.return_value = mock_job
    return job_id, brief_id, mock_session, mock_repo, mock_job


class TestProcessRenderJob:
    @patch("app.tasks.render._publish_progress")
    @patch("app.tasks.render._run_video_agent")
    @patch("app.tasks.render.BriefRepository")
    @patch("app.tasks.render.SessionLocal")
    @patch("app.tasks.render.RenderJobRepository")
    def test_happy_path_updates_status_to_done(
        self, mock_repo_cls, mock_session_cls, mock_brief_repo_cls,
        mock_run_agent, mock_publish,
    ):
        job_id, brief_id, mock_session, mock_repo, mock_job = _make_job_and_session()
        mock_session_cls.return_value = mock_session
        mock_repo_cls.return_value = mock_repo

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

    @patch("app.tasks.render._publish_progress")
    @patch("app.tasks.render._run_video_agent")
    @patch("app.tasks.render.BriefRepository")
    @patch("app.tasks.render.SessionLocal")
    @patch("app.tasks.render.RenderJobRepository")
    def test_publishes_progress_on_happy_path(
        self, mock_repo_cls, mock_session_cls, mock_brief_repo_cls,
        mock_run_agent, mock_publish,
    ):
        job_id, brief_id, mock_session, mock_repo, mock_job = _make_job_and_session()
        mock_session_cls.return_value = mock_session
        mock_repo_cls.return_value = mock_repo

        mock_brief_repo_cls.return_value.get_by_id.return_value = MagicMock()
        mock_run_agent.return_value = ("key", MagicMock(model_dump=lambda: {}))

        from app.tasks.render import process_render_job

        process_render_job(str(job_id))

        statuses = [c[1]["status"] for c in mock_publish.call_args_list]
        assert "rendering" in statuses
        assert "done" in statuses
        pcts = [c[1]["progress_pct"] for c in mock_publish.call_args_list]
        assert 5 in pcts
        assert 100 in pcts

    @patch("app.tasks.render._publish_progress")
    @patch("app.tasks.render._run_video_agent")
    @patch("app.tasks.render.BriefRepository")
    @patch("app.tasks.render.SessionLocal")
    @patch("app.tasks.render.RenderJobRepository")
    def test_publishes_failed_on_error(
        self, mock_repo_cls, mock_session_cls, mock_brief_repo_cls,
        mock_run_agent, mock_publish,
    ):
        job_id, brief_id, mock_session, mock_repo, mock_job = _make_job_and_session()
        mock_session_cls.return_value = mock_session
        mock_repo_cls.return_value = mock_repo

        mock_brief_repo_cls.return_value.get_by_id.return_value = MagicMock()
        mock_run_agent.side_effect = RuntimeError("agent exploded")

        from app.tasks.render import process_render_job

        with pytest.raises(RuntimeError):
            process_render_job(str(job_id))

        last_publish = mock_publish.call_args_list[-1]
        assert last_publish[1]["status"] == "failed"
        assert "agent exploded" in last_publish[1]["message"]

    @patch("app.tasks.render._publish_progress")
    @patch("app.tasks.render._run_video_agent")
    @patch("app.tasks.render.BriefRepository")
    @patch("app.tasks.render.SessionLocal")
    @patch("app.tasks.render.RenderJobRepository")
    def test_sets_failed_status_on_agent_error(
        self, mock_repo_cls, mock_session_cls, mock_brief_repo_cls,
        mock_run_agent, mock_publish,
    ):
        job_id, brief_id, mock_session, mock_repo, mock_job = _make_job_and_session()
        mock_session_cls.return_value = mock_session
        mock_repo_cls.return_value = mock_repo

        mock_brief = MagicMock(spec=CreativeBrief)
        mock_brief_repo_cls.return_value.get_by_id.return_value = mock_brief

        mock_run_agent.side_effect = RuntimeError("agent exploded")

        from app.tasks.render import process_render_job

        with pytest.raises(RuntimeError):
            process_render_job(str(job_id))

        failed_call = mock_repo.update.call_args_list[-1]
        assert failed_call[0][1]["status"] == "failed"
        assert "agent exploded" in failed_call[0][1]["error_message"]

    @patch("app.tasks.render._publish_progress")
    @patch("app.tasks.render.SessionLocal")
    @patch("app.tasks.render.RenderJobRepository")
    def test_raises_when_job_not_found(
        self, mock_repo_cls, mock_session_cls, mock_publish,
    ):
        job_id = uuid4()
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_repo = mock_repo_cls.return_value
        mock_repo.get_by_id.return_value = None

        from app.tasks.render import process_render_job

        with pytest.raises(ValueError, match="not found"):
            process_render_job(str(job_id))

    @patch("app.tasks.render._publish_progress")
    @patch("app.tasks.render._run_video_agent")
    @patch("app.tasks.render.BriefRepository")
    @patch("app.tasks.render.SessionLocal")
    @patch("app.tasks.render.RenderJobRepository")
    def test_always_closes_db_session(
        self, mock_repo_cls, mock_session_cls, mock_brief_repo_cls,
        mock_run_agent, mock_publish,
    ):
        job_id, brief_id, mock_session, mock_repo, mock_job = _make_job_and_session()
        mock_session_cls.return_value = mock_session
        mock_repo_cls.return_value = mock_repo

        mock_brief_repo_cls.return_value.get_by_id.return_value = MagicMock()
        mock_run_agent.return_value = ("path", MagicMock(model_dump=lambda: {}))

        from app.tasks.render import process_render_job

        process_render_job(str(job_id))

        mock_session.close.assert_called_once()

    @patch("app.tasks.render._publish_progress")
    @patch("app.tasks.render.SessionLocal")
    @patch("app.tasks.render.RenderJobRepository")
    def test_closes_session_even_on_error(
        self, mock_repo_cls, mock_session_cls, mock_publish,
    ):
        job_id = uuid4()
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_repo = mock_repo_cls.return_value
        mock_repo.get_by_id.return_value = None

        from app.tasks.render import process_render_job

        with pytest.raises(ValueError):
            process_render_job(str(job_id))

        mock_session.close.assert_called_once()

    @patch("app.tasks.render._publish_progress")
    @patch("app.tasks.render._run_video_agent")
    @patch("app.tasks.render.BriefRepository")
    @patch("app.tasks.render.SessionLocal")
    @patch("app.tasks.render.RenderJobRepository")
    def test_raises_when_brief_not_found(
        self, mock_repo_cls, mock_session_cls, mock_brief_repo_cls,
        mock_run_agent, mock_publish,
    ):
        job_id, brief_id, mock_session, mock_repo, mock_job = _make_job_and_session()
        mock_session_cls.return_value = mock_session
        mock_repo_cls.return_value = mock_repo

        mock_brief_repo_cls.return_value.get_by_id.return_value = None

        from app.tasks.render import process_render_job

        with pytest.raises(ValueError, match="CreativeBrief"):
            process_render_job(str(job_id))


class TestRunVideoAgentS3Wiring:
    @patch("app.tasks.render._cleanup_providers", new_callable=AsyncMock)
    @patch("app.tasks.render.SessionLocal")
    @patch("app.repositories.s3_client.get_s3_client")
    @patch("app.providers.image.get_image_provider")
    @patch("app.providers.music.get_music_provider")
    @patch("app.providers.tts.get_tts_provider")
    @patch("app.schemas.brief.BriefRead.model_validate")
    @patch("app.agents.video_agent.VideoAgent")
    def test_passes_s3_client_to_video_agent(
        self, mock_agent_cls, mock_validate, mock_tts,
        mock_music, mock_image, mock_get_s3,
        mock_session_cls, mock_cleanup,
    ):
        mock_s3 = MagicMock()
        mock_get_s3.return_value = mock_s3
        mock_session_cls.return_value = MagicMock()
        mock_validate.return_value = MagicMock()

        mock_agent = MagicMock()
        mock_agent.produce = AsyncMock(
            return_value=("key", MagicMock())
        )
        mock_agent_cls.return_value = mock_agent

        brief = MagicMock()

        from app.tasks.render import _run_video_agent

        _run_video_agent(brief, "job-1")

        mock_agent_cls.assert_called_once()
        call_kwargs = mock_agent_cls.call_args[1]
        assert call_kwargs["s3_client"] is mock_s3
