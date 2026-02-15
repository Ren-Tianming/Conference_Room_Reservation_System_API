# =====================================
# 必要モジュール
# =====================================

import datetime
from typing import Optional
from pydantic import BaseModel, Field

# =====================================
# User スキーマ
# =====================================

# ユーザー作成用
class UserCreate(BaseModel):
    user_name: str = Field(max_length=64)

# ユーザー取得用
class UserResponse(BaseModel):
    user_id: int
    user_name: str

    # ORMオブジェクトをJSON変換可能にする設定
    class Config:
        orm_mode = True

# ユーザー更新用
class UserUpdate(BaseModel):
    # Optional にすることで部分更新を可能にする
    user_name: Optional[str] = Field(default=None, max_length=64)

# =====================================
# ConferenceRoom スキーマ
# =====================================

# 会議室作成用
class ConferenceRoomCreate(BaseModel):
    conferenceroom_name: str = Field(max_length=32)
    conferenceroom_capacity: int = Field(gt=0)

# 会議室取得用
class ConferenceRoomResponse(BaseModel):
    conferenceroom_id: int
    conferenceroom_name: str
    conferenceroom_capacity: int

    # ORMオブジェクトをJSON変換可能にする設定
    class Config:
        orm_mode = True

# 会議室更新用
class ConferenceRoomUpdate(BaseModel):
    conferenceroom_name: Optional[str] = Field(default=None, max_length=32)
    conferenceroom_capacity: Optional[int] = Field(default=None, gt=0)

# =====================================
# Booking スキーマ
# =====================================

# 予約作成用
class BookingCreate(BaseModel):
    user_id: int
    conferenceroom_id: int
    booking_capacity: int = Field(gt=0)
    start_datetime: datetime.datetime
    end_datetime: datetime.datetime

# 予約取得用
class BookingResponse(BaseModel):
    booking_id: int
    user_id: int
    conferenceroom_id: int
    booking_capacity: int
    start_datetime: datetime.datetime
    end_datetime: datetime.datetime
    
    # ORMオブジェクトをJSON変換可能にする設定
    class Config:
        orm_mode = True

# 予約更新用
class BookingUpdate(BaseModel):
    user_id: Optional[int] = None
    conferenceroom_id: Optional[int] = None
    booking_capacity: Optional[int] = Field(default=None, gt=0)
    start_datetime: Optional[datetime.datetime] = None
    end_datetime: Optional[datetime.datetime] = None
