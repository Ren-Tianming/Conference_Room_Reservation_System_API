from typing import List
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from . import crud, models, schemas
from . database import SessionLocal, engine

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
@app.get("/users", response_model=List[schemas.User])
async def read_users(skip: int = 0, limit: int = 100, db:Session = Depends(get_db)):
    users = crud.get_users(db, skip=skip, limit=limit)
    return users

@app.get("/conferencerooms")
async def conferencerooms(conferencerooms: ConferenceRoom):
    return {"conferencerooms": conferencerooms}

@app.get("/bookings")
async def bookings(bookings: Booking):
    return {"bookings": bookings}

# Create
@app.post("/users")
async def users(users: User):
    return {"users": users}

@app.post("/conferencerooms")
async def conferencerooms(conferencerooms: ConferenceRoom):
    return {"conferencerooms": conferencerooms}

@app.post("/bookings")
async def bookings(bookings: Booking):
    return {"bookings": bookings}

