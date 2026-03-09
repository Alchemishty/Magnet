from uuid import uuid4

from app.models.asset import Asset
from app.models.brief import CreativeBrief
from app.models.job import RenderJob
from app.models.project import GameProfile, Project
from app.models.user import User


def create_test_user(**overrides) -> User:
    defaults = {
        "id": uuid4(),
        "email": f"test-{uuid4().hex[:8]}@example.com",
        "name": "Test User",
    }
    return User(**(defaults | overrides))


def create_test_project(**overrides) -> Project:
    defaults = {
        "id": uuid4(),
        "user_id": uuid4(),
        "name": "Test Game",
    }
    return Project(**(defaults | overrides))


def create_test_game_profile(**overrides) -> GameProfile:
    defaults = {
        "id": uuid4(),
        "project_id": uuid4(),
        "genre": "puzzle",
        "target_audience": "casual gamers",
        "core_mechanics": ["match-3"],
        "art_style": "cartoon",
        "brand_guidelines": {},
        "competitors": [],
        "key_selling_points": ["fun"],
    }
    return GameProfile(**(defaults | overrides))


def create_test_asset(**overrides) -> Asset:
    defaults = {
        "id": uuid4(),
        "project_id": uuid4(),
        "asset_type": "gameplay",
        "s3_key": f"uploads/{uuid4().hex}.mp4",
        "filename": "gameplay.mp4",
        "content_type": "video/mp4",
    }
    return Asset(**(defaults | overrides))


def create_test_brief(**overrides) -> CreativeBrief:
    defaults = {
        "id": uuid4(),
        "project_id": uuid4(),
        "hook_type": "fail_challenge",
        "narrative_angle": "Can you beat this?",
        "script": "Think you can do better?",
        "target_emotion": "curiosity",
        "cta_text": "Download now!",
    }
    return CreativeBrief(**(defaults | overrides))


def create_test_render_job(**overrides) -> RenderJob:
    defaults = {
        "id": uuid4(),
        "brief_id": uuid4(),
    }
    return RenderJob(**(defaults | overrides))
