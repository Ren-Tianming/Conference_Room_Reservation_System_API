from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BookingCreate(BaseModel):
    room_id: int
    title: str = Field(min_length=1, max_length=100)
    purpose: str | None = Field(default=None, max_length=255)
    attendee_count: int = Field(ge=1, le=500)
    start_time: datetime
    end_time: datetime

    @model_validator(mode='after')
    def validate_times(self) -> 'BookingCreate':
        if self.start_time >= self.end_time:
            raise ValueError('開始日時は終了日時より前である必要があります。')
        return self


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    purpose: str | None
    attendee_count: int
    start_time: datetime
    end_time: datetime
    status: str
    user_id: int
    room_id: int
    created_at: datetime
