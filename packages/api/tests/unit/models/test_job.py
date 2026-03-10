"""Tests for the RenderJob model."""

from uuid import uuid4

from sqlalchemy import inspect

from app.models.job import RenderJob


class TestRenderJob:
    def test_table_name(self):
        assert RenderJob.__tablename__ == "render_jobs"

    def test_has_required_columns(self):
        mapper = inspect(RenderJob)
        columns = {c.key for c in mapper.columns}

        assert "id" in columns
        assert "brief_id" in columns
        assert "status" in columns
        assert "composition" in columns
        assert "output_s3_key" in columns
        assert "render_duration_ms" in columns
        assert "error_message" in columns
        assert "celery_task_id" in columns

    def test_status_defaults_to_queued(self):
        job = RenderJob(brief_id=uuid4())

        assert job.status == "queued"

    def test_composition_accepts_layered_timeline(self):
        composition = {
            "duration": 15,
            "resolution": [1080, 1920],
            "fps": 30,
            "layers": [
                {
                    "type": "video",
                    "asset_id": "asset_123",
                    "start": 0,
                    "end": 8,
                },
                {
                    "type": "text",
                    "content": "Can you beat level 50?",
                    "start": 0,
                    "end": 3,
                },
            ],
        }
        job = RenderJob(brief_id=uuid4(), composition=composition)

        assert job.composition["duration"] == 15
        assert len(job.composition["layers"]) == 2

    def test_celery_task_id_defaults_to_none(self):
        job = RenderJob(brief_id=uuid4())

        assert job.celery_task_id is None

    def test_has_brief_relationship(self):
        assert hasattr(RenderJob, "brief")
