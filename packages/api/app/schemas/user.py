from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    email: str
    name: str
    clerk_id: str | None = None
    role: str = "creator"


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    name: str
    clerk_id: str | None
    role: str
    created_at: datetime
    updated_at: datetime | None


class UserUpdate(BaseModel):
    name: str | None = None
    role: str | None = None
