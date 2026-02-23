import datetime
from pydantic import BaseModel, Field

class User(BaseModel):
    user_id: int
    user_name: str = Field(max_length=64)

    class Config:
        from_attributes = True

class ConferenceRoom(BaseModel):
    conferenceroom_id: int
    conferenceroom_name: str = Field(max_length=32)
    conferenceroom_capacity: int = Field(..., gt=0)

    class Config:
        from_attributes = True

class Booking(BaseModel):
    booking_id: int = Field(...)
    user_id: int = Field(...)
    conferenceroom_id: int = Field(...)
    booking_capacity: int = Field(..., gt=0)
    start_datetime: datetime.datetime
    end_datetime: datetime.datetime
    
    class Config:
        from_attributes = True
        
class UserCreate(BaseModel):
    user_name: str = Field(..., max_length=64)

class ConferenceRoomCreate(BaseModel):
    conferenceroom_name: str = Field(..., max_length=32)
    conferenceroom_capacity: int = Field(..., gt=0)

class BookingCreate(BaseModel):
    user_id: int = Field(...)
    conferenceroom_id: int = Field(...)
    booking_capacity: int = Field(..., gt=0)
    start_datetime: datetime.datetime
    end_datetime: datetime.datetime

class UserUpdate(BaseModel):
    user_name: str = Field(..., max_length=64)

class ConferenceRoomUpdate(BaseModel):
    conferenceroom_name: str = Field(..., max_length=32)
    conferenceroom_capacity: int = Field(..., gt=0)

class BookingUpdate(BaseModel):
    user_id: int = Field(...)
    conferenceroom_id: int = Field(...)
    booking_capacity: int = Field(..., gt=0)
    start_datetime: datetime.datetime
    end_datetime: datetime.datetime