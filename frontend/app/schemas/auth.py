from datetime import datetime

from pydantic import BaseModel

from app.schemas.user import UserRead


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = 'bearer'
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime
    user: UserRead


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    access_token: str
    refresh_token: str | None = None
