from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BookingCreate(BaseModel):
    room_id: int
    title: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=1000)
    attendee_count: int = Field(gt=0)
    start_time: datetime
    end_time: datetime

    @model_validator(mode='after')
    def validate_time_range(self):
        if self.start_time >= self.end_time:
            raise ValueError('开始时间必须早于结束时间')
        return self


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    user_id: int
    room_id: int
    attendee_count: int
    start_time: datetime
    end_time: datetime
    status: str
