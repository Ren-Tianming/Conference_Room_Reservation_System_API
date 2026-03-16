from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import (
    authenticate_user,
    create_access_and_refresh_tokens,
    register_user,
    revoke_tokens,
    rotate_refresh_token,
)

router = APIRouter()


@router.post('/register', response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    user = register_user(db, payload)
    return UserRead.model_validate(user)


@router.post('/login', response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db, payload.username, payload.password)
    return create_access_and_refresh_tokens(db, user)


@router.post('/refresh', response_model=TokenResponse)
def refresh_token(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return rotate_refresh_token(db, payload.refresh_token)


@router.post('/logout', status_code=status.HTTP_200_OK)
def logout(
    payload: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    revoke_tokens(db, access_token=payload.access_token, refresh_token=payload.refresh_token, user_id=current_user.id)
    return {"message": "ログアウトしました。"}
