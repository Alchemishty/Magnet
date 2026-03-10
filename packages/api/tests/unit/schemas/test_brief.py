"""Tests for CreativeBrief schemas."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.brief import BriefCreate, BriefUpdate


class TestBriefCreate:
    def test_valid_creation(self):
        schema = BriefCreate(
            project_id=uuid4(),
            hook_type="fail_challenge",
            script="Can you beat level 50?",
        )

        assert schema.hook_type == "fail_challenge"
        assert schema.status == "draft"
        assert schema.generated_by == "agent"
        assert schema.target_format == "9:16"
        assert schema.target_duration == 15

    def test_rejects_invalid_status(self):
        with pytest.raises(ValidationError):
            BriefCreate(project_id=uuid4(), status="invalid")

    def test_rejects_invalid_generated_by(self):
        with pytest.raises(ValidationError):
            BriefCreate(project_id=uuid4(), generated_by="robot")

    def test_accepts_scene_plan(self):
        schema = BriefCreate(
            project_id=uuid4(),
            scene_plan={"scenes": [{"strategy": "COMPOSE", "duration": 5}]},
        )

        assert schema.scene_plan is not None


class TestBriefUpdate:
    def test_all_fields_optional(self):
        schema = BriefUpdate()

        assert schema.status is None
        assert schema.script is None

    def test_rejects_invalid_status(self):
        with pytest.raises(ValidationError):
            BriefUpdate(status="invalid")

    def test_accepts_valid_status_transition(self):
        schema = BriefUpdate(status="approved")

        assert schema.status == "approved"
