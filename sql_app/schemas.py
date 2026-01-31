import datetime
from pydantic import BaseModel, Field

class Booking(BaseModel):
    booking_id: int
    user_id: int
    conferenceroom_id: int 
    booked_capacity: int
    start_datetime: datetime.datetime
    end_datetime: datetime.datetime
    
    class Config:
        orm_mode = True

class User(BaseModel):
    user_id: int
    user_name: str = Field(max_length=64)

class ConferenceRoom(BaseModel):
    conferenceroom_id: int
    conferenceroom_name: str = Field(max_length=32)
    capacity: int
