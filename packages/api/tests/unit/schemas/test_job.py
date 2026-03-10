"""Tests for RenderJob schemas."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.composition import Composition, CompositionLayer
from app.schemas.job import JobCreate, JobUpdate


class TestJobCreate:
    def test_valid_creation(self):
        schema = JobCreate(brief_id=uuid4())

        assert schema.status == "queued"
        assert schema.composition is None

    def test_with_composition(self):
        comp = Composition(
            duration=15,
            resolution=[1080, 1920],
            layers=[CompositionLayer(type="video", start=0, end=8)],
        )
        schema = JobCreate(brief_id=uuid4(), composition=comp)

        assert schema.composition.duration == 15

    def test_rejects_invalid_status(self):
        with pytest.raises(ValidationError):
            JobCreate(brief_id=uuid4(), status="invalid")


class TestJobUpdate:
    def test_all_fields_optional(self):
        schema = JobUpdate()

        assert schema.status is None
        assert schema.composition is None

    def test_status_update(self):
        schema = JobUpdate(status="rendering")

        assert schema.status == "rendering"

    def test_celery_task_id_update(self):
        schema = JobUpdate(celery_task_id="abc-123")

        assert schema.celery_task_id == "abc-123"

    def test_rejects_invalid_status(self):
        with pytest.raises(ValidationError):
            JobUpdate(status="broken")
