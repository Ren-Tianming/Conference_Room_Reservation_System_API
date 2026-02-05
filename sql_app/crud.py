from sqlalchemy.orm import Session
from . import models, schemas

# ユーザー一覧を取得する関数
def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

# 会議室一覧を取得する関数
def get_conferencerooms(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ConferenceRoom).offset(skip).limit(limit).all()

# 予約一覧を取得する関数
def get_bookings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Booking).offset(skip).limit(limit).all()

# ユーザー登録する関数
def create_user(db: Session, user: schemas.UserCreate):
    db_user = models.User(user_name = user.user_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# 会議室登録する関数
def create_conferenceroom(db: Session, conferenceroom: schemas.ConferenceRoomCreate):
    db_conferenceroom = models.ConferenceRoom(
        conferenceroom_name = conferenceroom.conferenceroom_name,
        conferenceroom_capacity = conferenceroom.conferenceroom_capacity
    )
    db.add(db_conferenceroom)
    db.commit()
    db.refresh(db_conferenceroom)
    return db_conferenceroom

# 予約登録する関数
def create_booking(db:Session, booking: schemas.BookingCreate):
    db_booking = models.Booking(**booking.dict())
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)
    return db_booking