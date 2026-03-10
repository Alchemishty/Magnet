"""Execution plan schemas — Video Agent internal state."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.schemas.scene_plan import SceneStrategy

PreparedStatus = Literal["pending", "ready", "failed"]
AudioType = Literal["voiceover", "music"]


class PreparedScene(BaseModel):
    index: int
    strategy: SceneStrategy
    status: PreparedStatus = "pending"
    output_path: str | None = None
    error_message: str | None = None


class PreparedAudio(BaseModel):
    type: AudioType
    status: PreparedStatus = "pending"
    output_path: str | None = None
    error_message: str | None = None


class ExecutionPlan(BaseModel):
    brief_id: UUID
    project_id: UUID
    scenes: list[PreparedScene]
    audio: list[PreparedAudio] = []
    work_dir: str

    @field_validator("scenes")
    @classmethod
    def scenes_must_not_be_empty(cls, v: list[PreparedScene]) -> list[PreparedScene]:
        if len(v) == 0:
            raise ValueError("execution plan must have at least one scene")
        return v
