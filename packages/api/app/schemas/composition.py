from typing import Literal

from pydantic import BaseModel, ConfigDict


class CompositionLayer(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    type: Literal["video", "text", "audio", "image"]
    start: float
    end: float
    asset_id: str | None = None
    content: str | None = None
    font: str | None = None
    position: list[int] | str | None = None
    trim: list[float] | None = None
    effects: list[str] | None = None
    animation: str | None = None
    volume: float | None = None


class Composition(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    duration: float
    resolution: list[int]
    fps: int = 30
    layers: list[CompositionLayer]
