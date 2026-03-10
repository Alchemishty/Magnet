from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

BriefStatus = Literal["draft", "approved", "producing", "complete"]
GeneratedBy = Literal["agent", "human"]


class BriefCreate(BaseModel):
    project_id: UUID
    hook_type: str | None = None
    narrative_angle: str | None = None
    script: str | None = None
    voiceover_text: str | None = None
    target_emotion: str | None = None
    cta_text: str | None = None
    reference_ads: list | None = None
    target_format: str = "9:16"
    target_duration: int = 15
    status: BriefStatus = "draft"
    generated_by: GeneratedBy = "agent"
    scene_plan: dict | None = None


class BriefRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    hook_type: str | None
    narrative_angle: str | None
    script: str | None
    voiceover_text: str | None
    target_emotion: str | None
    cta_text: str | None
    reference_ads: list
    target_format: str
    target_duration: int
    status: str
    generated_by: str
    scene_plan: dict | None
    created_at: datetime
    updated_at: datetime | None


class BriefUpdate(BaseModel):
    hook_type: str | None = None
    narrative_angle: str | None = None
    script: str | None = None
    voiceover_text: str | None = None
    target_emotion: str | None = None
    cta_text: str | None = None
    reference_ads: list | None = None
    target_format: str | None = None
    target_duration: int | None = None
    status: BriefStatus | None = None
    scene_plan: dict | None = None
