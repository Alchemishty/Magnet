"""Scene plan schemas — structured input from CreativeBrief.scene_plan."""

from typing import Literal

from pydantic import BaseModel, field_validator


SceneStrategy = Literal["COMPOSE", "GENERATE", "RENDER"]


class Scene(BaseModel):
    strategy: SceneStrategy
    type: str
    duration: float
    asset_query: str | None = None
    generator: str | None = None
    prompt: str | None = None
    template: str | None = None
    params: dict | None = None
    font: str | None = None

    @field_validator("duration")
    @classmethod
    def duration_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("duration must be positive")
        return v


class VoiceoverPlan(BaseModel):
    strategy: SceneStrategy
    generator: str
    script: str
    voice: str | None = None


class MusicPlan(BaseModel):
    strategy: SceneStrategy
    generator: str
    prompt: str


class AudioPlan(BaseModel):
    voiceover: VoiceoverPlan | None = None
    music: MusicPlan | None = None


class ScenePlan(BaseModel):
    scenes: list[Scene]
    audio: AudioPlan | None = None

    @field_validator("scenes")
    @classmethod
    def scenes_must_not_be_empty(cls, v: list[Scene]) -> list[Scene]:
        if len(v) == 0:
            raise ValueError("scene plan must have at least one scene")
        return v
