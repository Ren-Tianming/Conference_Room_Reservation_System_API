from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = 'admin'
    USER = 'user'


class BookingStatus(StrEnum):
    CONFIRMED = 'confirmed'
    CANCELLED = 'cancelled'
