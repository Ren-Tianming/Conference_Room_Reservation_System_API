# =========================================
# 必要モジュール
# =========================================

from sqlalchemy.orm import Session
from . import models, schemas
from sqlalchemy.exc import IntegrityError
from .exceptions import AlreadyExistsError, NotFoundError, BookingConflictError

# =========================================
# User CRUD
# =========================================

# ユーザーを作成する関数
def create_user(db: Session, user: schemas.UserCreate):
    # ORMオブジェクト生成
    db_user = models.User(user_name = user.user_name)

    try:
        # セッションへ追加
        db.add(db_user)
        # DBへ反映
        db.commit()
        # 最新状態取得（IDなど）
        db.refresh(db_user)
        return db_user
    
    except IntegrityError:
        db.rollback()
        raise AlreadyExistsError("User already exists")

# ユーザー一覧を取得する関数
def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()

# 特定ユーザーを取得する関数
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(
        models.User.user_id == user_id
    ).first()

# ユーザーを更新する関数
def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate):
    db_user = get_user(db, user_id)

    if not db_user:
        raise NotFoundError("User not found")

    update_data = user_update.dict(exclude_unset=True)

    for key, value in update_data.items():
        setattr(db_user, key, value)

    try:
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise AlreadyExistsError("User already exists")

# ユーザーを削除する関数
def delete_user(db: Session, user_id: int):
    db_user = get_user(db, user_id)

    if not db_user:
        raise NotFoundError("User not found")

    db.delete(db_user)
    db.commit()

    return db_user

# =========================================
# Conferenceroom CRUD
# =========================================

# 会議室を作成する関数
def create_conferenceroom(db: Session, conferenceroom: schemas.ConferenceRoomCreate):
    # ORMオブジェクト生成
    db_conferenceroom = models.ConferenceRoom(
        conferenceroom_name = conferenceroom.conferenceroom_name,
        conferenceroom_capacity = conferenceroom.conferenceroom_capacity
    )

    try:
        # セッションへ追加
        db.add(db_conferenceroom)
        # DBへ反映
        db.commit()
        # 最新状態取得（IDなど）
        db.refresh(db_conferenceroom)
        return db_conferenceroom
    except IntegrityError:
        db.rollback()
        raise AlreadyExistsError("Conferenceroom already exists")

# 会議室一覧を取得する関数
def get_conferencerooms(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.ConferenceRoom).offset(skip).limit(limit).all()

# 特定会議室を取得する関数
def get_conferenceroom(db: Session, conferenceroom_id: int):
    return db.query(models.ConferenceRoom).filter(
        models.ConferenceRoom.conferenceroom_id == conferenceroom_id
    ).first()

# 会議室を更新する関数
def update_conferenceroom(db: Session, conferenceroom_id: int, conferenceroom_update: schemas.ConferenceRoomUpdate):
    # 対象会議室取得
    db_conferenceroom = get_conferenceroom(db, conferenceroom_id)
    if not db_conferenceroom:
        raise NotFoundError("Conferenceroom not found")
    # dict化（None除外）
    update_data = conferenceroom_update.dict(exclude_unset=True)
    # フィールドごとに更新
    for key, value in update_data.items():
        setattr(db_conferenceroom, key, value)
    
    try:
        db.commit()
        # 最新状態取得（IDなど）
        db.refresh(db_conferenceroom)
        return db_conferenceroom
    except IntegrityError:
        db.rollback()
        raise AlreadyExistsError("Conferenceroom already exists")

# 会議室を削除する関数
def delete_conferenceroom(db: Session, conferenceroom_id: int):
    db_conferenceroom = get_conferenceroom(db, conferenceroom_id)

    if not db_conferenceroom:
        raise NotFoundError("Conferenceroom not found")
    
    db.delete(db_conferenceroom)
    db.commit()
    
    return db_conferenceroom

# =========================================
# Booking CRUD
# =========================================

# 予約を作成する関数
def create_booking(db: Session, booking: schemas.BookingCreate):

    # 时间合法性检查
    if booking.start_datetime >= booking.end_datetime:
        raise ValueError("Invalid time range")

    # 冲突检查
    existing_booking = db.query(models.Booking).filter(
        models.Booking.conferenceroom_id == booking.conferenceroom_id,
        models.Booking.start_datetime < booking.end_datetime,
        models.Booking.end_datetime > booking.start_datetime
    ).first()

    if existing_booking:
        raise BookingConflictError("Time slot already booked")

    db_booking = models.Booking(
        user_id=booking.user_id,
        conferenceroom_id=booking.conferenceroom_id,
        booking_capacity=booking.booking_capacity,
        start_datetime=booking.start_datetime,
        end_datetime=booking.end_datetime
    )

    try:
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
        return db_booking

    except IntegrityError:
        db.rollback()
        raise AlreadyExistsError("Booking already exists")


# 予約一覧を取得する関数
def get_bookings(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Booking).offset(skip).limit(limit).all()


# 特定予約を取得
def get_booking(db: Session, booking_id: int):
    return db.query(models.Booking).filter(
        models.Booking.booking_id == booking_id
    ).first()


# 予約を更新する関数
def update_booking(
    db: Session,
    booking_id: int,
    booking_update: schemas.BookingUpdate
):

    db_booking = get_booking(db, booking_id)
    if not db_booking:
        raise NotFoundError("Booking not found")

    update_data = booking_update.dict(exclude_unset=True)

    # 先に値を適用
    for key, value in update_data.items():
        setattr(db_booking, key, value)

    # 时间合法性检查
    if db_booking.start_datetime >= db_booking.end_datetime:
        raise ValueError("Invalid time range")

    # 冲突检查（排除自身）
    existing_booking = db.query(models.Booking).filter(
        models.Booking.conferenceroom_id == db_booking.conferenceroom_id,
        models.Booking.booking_id != booking_id,
        models.Booking.start_datetime < db_booking.end_datetime,
        models.Booking.end_datetime > db_booking.start_datetime
    ).first()

    if existing_booking:
        raise BookingConflictError("Time slot already booked")

    try:
        db.commit()
        db.refresh(db_booking)
        return db_booking

    except IntegrityError:
        db.rollback()
        raise AlreadyExistsError("Booking already exists")


# 予約を削除する関数
def delete_booking(db: Session, booking_id: int):

    db_booking = get_booking(db, booking_id)
    if not db_booking:
        raise NotFoundError("Booking not found")

    db.delete(db_booking)
    db.commit()

    return db_booking
