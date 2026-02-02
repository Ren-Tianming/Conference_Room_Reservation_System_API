from typing import List
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create.all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

"""
@app.get("/")
async def index():
    return {"message": "Success!"}
"""

# Read
@app.get("/users", response_model = List[schemas.User])
async def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@app.get("/conferencerooms", response_model = List[schemas.ConferenceRoom])
async def read_conferencerooms(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    conferencerooms = crud.get_conferencerooms(db, skip=skip, limit=limit)
    return conferencerooms

@app.get("/bookings", response_model = List[schemas.Booking])
async def read_bookings(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    bookings = crud.get_bookings(db, skip=skip, limit=limit)
    return bookings

# Create
@app.post("/users",response_model=schemas.User)
async def create_user(user: schemas.User, db: Session = Depends(get_db)):
    return crud,create_user(db = db, user = user)

@app.post("/conferencerooms",response_model=schemas.ConferenceRoom)
async def create_conferenceroom(conferenceroom: schemas.ConferenceRoom, db: Session = Depends(get_db)):
    return crud,create_conferenceroom(db = db, conferenceroom = conferenceroom)

@app.post("/bookings",response_model=schemas.Booking)
async def create_booking(booking: schemas.Booking, db: Session = Depends(get_db)):
    return crud,create_booking(db = db, booking = booking)