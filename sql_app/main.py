from fastapi import FastAPI
from routers import conferencerooms, bookings, users
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Conference Room Booking System",
    description="会議室予約システム API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "会議室予約システムへようこそ！"}

app.include_router(users.router)
app.include_router(conferencerooms.router)
app.include_router(bookings.router)