from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..schemas import schemas
from ..models import models
from fastapi import HTTPException

# ユーザーを登録
async def create_user(db: AsyncSession, user: schemas.UserCreate):
    db_user = models.User(user_name=user.user_name)
    db.add(db_user)
    try:
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except Exception:
        await db.rollback()
        raise

# ユーザー一覧を取得
async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.User).offset(skip).limit(limit))
    return result.scalars().all()

# 特定のユーザーを取得
async def get_user(db: AsyncSession, user_id: int):
    result = await db.get(models.User, user_id)
    return result

# ユーザーを更新
async def update_user(db: AsyncSession, user_id: int, user: schemas.UserUpdate):
    db_user = await db.get(models.User, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.user_name = user.user_name
    try:
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update user")

# ユーザーを削除
async def delete_user(db: AsyncSession, user_id: int):
    db_user = await db.get(models.User, user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    await db.delete(db_user)
    try:
        await db.commit()
        return {"detail": "User deleted"}
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete user")
    
# 会議室を登録
async def create_conferenceroom(db: AsyncSession, conferenceroom: schemas.ConferenceRoom):
    db_conferenceroom = models.ConferenceRoom(**conferenceroom.model_dump()) # dict() 换成 model_dump()
    db.add(db_conferenceroom)
    try:
        await db.commit()
        await db.refresh(db_conferenceroom)
        return db_conferenceroom
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create conferenceroom")

# 会議室一覧を取得
async def get_conferencerooms(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.ConferenceRoom).offset(skip).limit(limit))
    return result.scalars().all()

# 特定の会議室を取得
async def get_conferenceroom(db: AsyncSession, conferenceroom_id: int):
    result = await db.get(models.ConferenceRoom, conferenceroom_id)
    return result

# 会議室を更新
async def update_conferenceroom(db: AsyncSession, conferenceroom_id: int, conferenceroom: schemas.ConferenceRoomUpdate):
    db_conferenceroom = await db.get(models.ConferenceRoom, conferenceroom_id)
    if db_conferenceroom is None:
        raise HTTPException(status_code=404, detail="Conference room not found")
    db_conferenceroom.conferenceroom_name = conferenceroom.conferenceroom_name
    db_conferenceroom.conferenceroom_capacity = conferenceroom.conferenceroom_capacity
    try:
        await db.commit()
        await db.refresh(db_conferenceroom)
        return db_conferenceroom
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update conferenceroom")  
    
# 会議室を削除
async def delete_conferenceroom(db: AsyncSession, conferenceroom_id: int):
    db_conferenceroom = await db.get(models.ConferenceRoom, conferenceroom_id)
    if db_conferenceroom is None:
        raise HTTPException(status_code=404, detail="Conference room not found")
    await db.delete(db_conferenceroom)
    try:
        await db.commit()
        return {"detail": "Conference room deleted"}
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete conferenceroom")
    
# 予約登録（重複チェックの修正）
async def create_booking(db: AsyncSession, booking: schemas.BookingCreate):
    # 重複チェックも select() を使用
    query = select(models.Booking).filter(
        models.Booking.conferenceroom_id == booking.conferenceroom_id,
        models.Booking.start_datetime < booking.end_datetime,
        models.Booking.end_datetime > booking.start_datetime
    )
    result = await db.execute(query)
    db_booked = result.scalars().first()
    
    if not db_booked:
        db_booking = models.Booking(**booking.model_dump()) # dict() 换成 model_dump()
        db.add(db_booking)
        try:
            await db.commit()
            await db.refresh(db_booking)
            return db_booking
        except Exception:
            await db.rollback()
            raise
    else:
        raise HTTPException(status_code=409, detail="Already booked")
    
# 予約一覧を取得
async def get_bookings(db: AsyncSession, skip: int = 0, limit: int = 100):
    result = await db.execute(select(models.Booking).offset(skip).limit(limit))
    return result.scalars().all()

# 特定の予約を取得
async def get_booking(db: AsyncSession, booking_id: int):
    result = await db.get(models.Booking, booking_id)
    return result

# 予約を更新
async def update_booking(db: AsyncSession, booking_id: int, booking: schemas.BookingUpdate):
    db_booking = await db.get(models.Booking, booking_id)
    if db_booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    db_booking.user_id = booking.user_id
    db_booking.conferenceroom_id = booking.conferenceroom_id
    db_booking.booking_capacity = booking.booking_capacity
    db_booking.start_datetime = booking.start_datetime
    db_booking.end_datetime = booking.end_datetime
    try:
        await db.commit()
        await db.refresh(db_booking)
        return db_booking
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update booking")
    
# 予約を削除
async def delete_booking(db: AsyncSession, booking_id: int):
    db_booking = await db.get(models.Booking, booking_id)
    if db_booking is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    await db.delete(db_booking)
    try:
        await db.commit()
        return {"detail": "Booking deleted"}
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete booking") 
