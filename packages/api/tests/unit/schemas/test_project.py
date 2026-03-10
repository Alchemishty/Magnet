"""Tests for Project and GameProfile schemas."""

from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.project import (
    GameProfileCreate,
    GameProfileRead,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
)


class TestProjectCreate:
    def test_valid_creation(self):
        uid = uuid4()
        schema = ProjectCreate(name="My Game", user_id=uid)

        assert schema.name == "My Game"
        assert schema.user_id == uid

    def test_rejects_missing_name(self):
        with pytest.raises(ValidationError):
            ProjectCreate(user_id=uuid4())


class TestProjectRead:
    def test_from_attributes(self):
        now = datetime.now(timezone.utc)
        obj = SimpleNamespace(
            id=uuid4(),
            user_id=uuid4(),
            name="Game",
            status="active",
            created_at=now,
            updated_at=None,
        )

        schema = ProjectRead.model_validate(obj, from_attributes=True)

        assert schema.name == "Game"
        assert schema.status == "active"


class TestProjectUpdate:
    def test_all_fields_optional(self):
        schema = ProjectUpdate()

        assert schema.name is None
        assert schema.status is None


class TestGameProfileCreate:
    def test_valid_creation(self):
        schema = GameProfileCreate(
            project_id=uuid4(),
            genre="puzzle",
            core_mechanics=["match-3"],
            brand_guidelines={"colors": ["blue"]},
        )

        assert schema.genre == "puzzle"
        assert schema.core_mechanics == ["match-3"]

    def test_all_fields_optional_except_project_id(self):
        schema = GameProfileCreate(project_id=uuid4())

        assert schema.genre is None
        assert schema.core_mechanics is None

    def test_rejects_missing_project_id(self):
        with pytest.raises(ValidationError):
            GameProfileCreate(genre="puzzle")


class TestGameProfileRead:
    def test_from_attributes(self):
        now = datetime.now(timezone.utc)
        obj = SimpleNamespace(
            id=uuid4(),
            project_id=uuid4(),
            genre="rpg",
            target_audience="18-35",
            core_mechanics=["combat"],
            art_style="anime",
            brand_guidelines={},
            competitors=["Game X"],
            key_selling_points=["story"],
            created_at=now,
            updated_at=None,
        )

        schema = GameProfileRead.model_validate(obj, from_attributes=True)

        assert schema.genre == "rpg"
        assert schema.core_mechanics == ["combat"]
