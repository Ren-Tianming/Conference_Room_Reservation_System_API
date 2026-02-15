from typing import List
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create
@app.post("/users", response_model=schemas.UserResponse)
async def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    return crud.create_user(db=db, user=user)

@app.post("/conferencerooms", response_model=schemas.ConferenceRoomResponse)
async def create_conferenceroom(conferenceroom: schemas.ConferenceRoomCreate, db: Session = Depends(get_db)):
    return crud.create_conferenceroom(db=db, conferenceroom=conferenceroom)

@app.post("/bookings", response_model=schemas.BookingResponse)
async def create_booking(booking: schemas.BookingCreate, db: Session = Depends(get_db)):
    return crud.create_booking(db=db, booking=booking)

# Read
@app.get("/users", response_model = List[schemas.UserResponse])
async def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@app.get("/conferencerooms", response_model = List[schemas.ConferenceRoomResponse])
async def read_conferencerooms(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    conferencerooms = crud.get_conferencerooms(db, skip=skip, limit=limit)
    return conferencerooms

@app.get("/bookings", response_model = List[schemas.BookingResponse])
async def read_bookings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    bookings = crud.get_bookings(db, skip=skip, limit=limit)
    return bookings

# Delete
@app.delete("/users/{user_id}", response_model=schemas.UserResponse)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    return crud.delete_user(db=db, user_id=user_id)

@app.delete("/conferencerooms/{conferenceroom_id}", response_model=schemas.ConferenceRoomResponse)
async def delete_conferenceroom(conferenceroom_id: int, db: Session = Depends(get_db)):
    return crud.delete_conferenceroom(db=db, conferenceroom_id=conferenceroom_id)

@app.delete("/bookings/{booking_id}", response_model=schemas.BookingResponse)
async def delete_booking(booking_id: int, db: Session = Depends(get_db)):
    return crud.delete_booking(db=db, booking_id=booking_id)
