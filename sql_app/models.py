# =====================================
# 必要なモジュールをインポート
# =====================================

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from .database import Base


# =====================================
# User テーブル
# =====================================

class User(Base):
    # DB上のテーブル名
    __tablename__ = "users"

    # ユーザーID（主キー）
    user_id = Column(Integer, primary_key=True, index=True)

    # ユーザー名（重複禁止）
    user_name = Column(String, unique=True, index=True)


# =====================================
# ConferenceRoom テーブル
# =====================================

class ConferenceRoom(Base):
    __tablename__ = "conferencerooms"

    # 会議室ID（主キー）
    conferenceroom_id = Column(Integer, primary_key=True, index=True)

    # 会議室名（重複不可）
    conferenceroom_name = Column(String, unique=True, index=True)

    # 収容人数（NULL不可）
    conferenceroom_capacity = Column(Integer, nullable=False)


# =====================================
# Booking テーブル（予約）
# =====================================

class Booking(Base):
    __tablename__ = "bookings"

    # ----------------------------
    # リレーション定義
    # ----------------------------

    # Userオブジェクトへアクセス可能
    user = relationship("User")

    # ConferenceRoomオブジェクトへアクセス可能
    conferenceroom = relationship("ConferenceRoom")

    # ----------------------------
    # カラム定義
    # ----------------------------

    # 予約ID（主キー）
    booking_id = Column(Integer, primary_key=True, index=True)

    # ユーザー外部キー
    user_id = Column(
        Integer,
        ForeignKey("users.user_id", ondelete="RESTRICT"),
        nullable=False
    )

    # 会議室外部キー
    conferenceroom_id = Column(
        Integer,
        ForeignKey("conferencerooms.conferenceroom_id", ondelete="RESTRICT"),
        nullable=False
    )

    # 予約人数
    booking_capacity = Column(Integer, nullable=False)

    # 開始日時
    start_datetime = Column(DateTime, nullable=False)

    # 終了日時
    end_datetime = Column(DateTime, nullable=False)
