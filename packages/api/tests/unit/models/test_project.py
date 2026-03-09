"""Tests for the Project and GameProfile models."""

from sqlalchemy import inspect

from app.models.project import GameProfile, Project


class TestProject:
    def test_table_name(self):
        assert Project.__tablename__ == "projects"

    def test_has_required_columns(self):
        mapper = inspect(Project)
        columns = {c.key for c in mapper.columns}

        assert "id" in columns
        assert "user_id" in columns
        assert "name" in columns
        assert "status" in columns

    def test_user_id_is_not_nullable(self):
        mapper = inspect(Project)
        col = mapper.columns["user_id"]

        assert col.nullable is False

    def test_status_defaults_to_active(self):
        from uuid import uuid4

        project = Project(
            user_id=uuid4(), name="Test Game"
        )

        assert project.status == "active"

    def test_has_relationships(self):
        assert hasattr(Project, "user")
        assert hasattr(Project, "game_profile")
        assert hasattr(Project, "assets")
        assert hasattr(Project, "briefs")


class TestGameProfile:
    def test_table_name(self):
        assert GameProfile.__tablename__ == "game_profiles"

    def test_has_required_columns(self):
        mapper = inspect(GameProfile)
        columns = {c.key for c in mapper.columns}

        assert "id" in columns
        assert "project_id" in columns
        assert "genre" in columns
        assert "target_audience" in columns
        assert "core_mechanics" in columns
        assert "art_style" in columns
        assert "brand_guidelines" in columns
        assert "competitors" in columns
        assert "key_selling_points" in columns

    def test_project_id_is_unique(self):
        mapper = inspect(GameProfile)
        col = mapper.columns["project_id"]

        assert col.unique is True

    def test_jsonb_fields_accept_dicts(self):
        from uuid import uuid4

        profile = GameProfile(
            project_id=uuid4(),
            brand_guidelines={"colors": ["red"]},
            core_mechanics=["match-3", "puzzle"],
            competitors=["Game A"],
            key_selling_points=["fun"],
        )

        assert profile.brand_guidelines == {"colors": ["red"]}
        assert profile.core_mechanics == ["match-3", "puzzle"]
