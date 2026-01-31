import datetime
from fastapi import FastAPI
from pydantic import BaseModel, Field

class Booking(BaseModel):
    booking_id: int
    user_id: int
    conferenceroom_id: int 
    booked_capacity: int
    start_datetime: datetime.datetime
    end_datetime: datetime.datetime

class User(BaseModel):
    user_id: int
    user_name: str = Field(max_length=64)

class ConferenceRoom(BaseModel):
    conferenceroom_id: int
    conferenceroom_name: str = Field(max_length=32)
    capacity: int

app = FastAPI()

@app.get("/")
async def index():
    return {"message": "Success!"}

@app.post("/users")
async def users(users: User):
    return {"users": users}

@app.post("/conferencerooms")
async def conferencerooms(conferencerooms: ConferenceRoom):
    return {"conferencerooms": conferencerooms}

@app.post("/bookings")
async def bookings(bookings: Booking):
    return {"bookings": bookings}

