from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class RoomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    location: str | None = Field(default=None, max_length=128)
    capacity: int = Field(gt=0)


class RoomUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=64)
    location: str | None = Field(default=None, max_length=128)
    capacity: int | None = Field(default=None, gt=0)
    is_active: bool | None = None


class RoomRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    location: str | None
    capacity: int
    is_active: bool


class RoomScheduleItem(BaseModel):
    booking_id: int
    title: str
    start_time: datetime
    end_time: datetime
    attendee_count: int
    status: str


class RoomScheduleResponse(BaseModel):
    room_id: int
    room_name: str
    day: str
    bookings: list[RoomScheduleItem]
