from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.config import settings


class BookingCreate(BaseModel):
    room_id: int
    title: str = Field(min_length=1, max_length=100)
    purpose: Optional[str] = Field(default=None, max_length=255)
    attendee_count: int = Field(ge=1, le=500)
    start_time: datetime
    end_time: datetime

    @model_validator(mode='after')
    def validate_times(self) -> 'BookingCreate':
        if self.start_time.tzinfo is None or self.start_time.utcoffset() is None:
            raise ValueError('開始日時には timezone を含めてください。')
        if self.end_time.tzinfo is None or self.end_time.utcoffset() is None:
            raise ValueError('終了日時には timezone を含めてください。')

        self.start_time = self.start_time.astimezone(timezone.utc)
        self.end_time = self.end_time.astimezone(timezone.utc)

        if self.start_time >= self.end_time:
            raise ValueError('開始日時は終了日時より前である必要があります。')
        if self.start_time <= datetime.now(timezone.utc):
            raise ValueError('開始日時は現在時刻より後である必要があります。')
        max_duration = timedelta(hours=settings.max_booking_duration_hours)
        if self.end_time - self.start_time > max_duration:
            raise ValueError(f'予約時間は最大 {settings.max_booking_duration_hours} 時間までです。')
        return self


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    purpose: Optional[str]
    attendee_count: int
    start_time: datetime
    end_time: datetime
    status: str
    user_id: int
    room_id: int
    created_at: datetime
