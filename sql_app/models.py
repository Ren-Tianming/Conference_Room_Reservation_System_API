from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from .database import Base

class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key = True,index = True)
    user_name = Column(String, unique = True, index = True)

class ConferenceRoom(Base):
    __tablename__ = 'conferencerooms'
    conferenceroom_id = Column(Integer, primary_key = True,index = True)
    conferenceroom_name = Column(String, unique = True, index = True)
    conferenceroom_capacity = Column(Integer, nullable=False)

class Booking(Base):
    __tablename__ = 'bookings'
    booking_id = Column(Integer, primary_key = True,index = True)
    user_id = Column(
        Integer, 
        ForeignKey('users.user_id', ondelete = 'SET NULL'), 
        nullable = True
        )
    conferenceroom_id = Column(
        Integer, 
        ForeignKey('conferencerooms.conferenceroom_id', ondelete = 'SET NULL'), 
        nullable = True
        )
    booking_capacity = Column(Integer, nullable = False)
    start_datetime = Column(DateTime, nullable = False)
    end_datetime = Column(DateTime, nullable = False)