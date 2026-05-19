from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    capacity: int = Field(ge=1, le=500)
    location: str = Field(default='本社', max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)


class RoomRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    capacity: int
    location: str
    description: Optional[str]
    created_at: datetime
