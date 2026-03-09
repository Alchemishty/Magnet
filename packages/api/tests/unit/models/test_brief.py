"""Tests for the CreativeBrief model."""

from uuid import uuid4

from sqlalchemy import inspect

from app.models.brief import CreativeBrief


class TestCreativeBrief:
    def test_table_name(self):
        assert CreativeBrief.__tablename__ == "creative_briefs"

    def test_has_required_columns(self):
        mapper = inspect(CreativeBrief)
        columns = {c.key for c in mapper.columns}

        assert "id" in columns
        assert "project_id" in columns
        assert "hook_type" in columns
        assert "narrative_angle" in columns
        assert "script" in columns
        assert "voiceover_text" in columns
        assert "target_emotion" in columns
        assert "cta_text" in columns
        assert "reference_ads" in columns
        assert "target_format" in columns
        assert "target_duration" in columns
        assert "status" in columns
        assert "generated_by" in columns
        assert "scene_plan" in columns

    def test_status_defaults_to_draft(self):
        brief = CreativeBrief(project_id=uuid4())

        assert brief.status == "draft"

    def test_generated_by_defaults_to_agent(self):
        brief = CreativeBrief(project_id=uuid4())

        assert brief.generated_by == "agent"

    def test_target_format_defaults_to_9_16(self):
        brief = CreativeBrief(project_id=uuid4())

        assert brief.target_format == "9:16"

    def test_target_duration_defaults_to_15(self):
        brief = CreativeBrief(project_id=uuid4())

        assert brief.target_duration == 15

    def test_scene_plan_accepts_dict(self):
        brief = CreativeBrief(
            project_id=uuid4(),
            scene_plan={"scenes": [{"strategy": "COMPOSE"}]},
        )

        assert brief.scene_plan["scenes"][0]["strategy"] == "COMPOSE"

    def test_has_relationships(self):
        assert hasattr(CreativeBrief, "project")
        assert hasattr(CreativeBrief, "render_jobs")
