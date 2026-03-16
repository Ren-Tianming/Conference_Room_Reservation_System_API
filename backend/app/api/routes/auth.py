from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.db.redis_client import get_redis
from app.models.user import User
from app.schemas.auth import LogoutRequest, RefreshTokenRequest, TokenPair
from app.schemas.common import MessageResponse
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import (
    authenticate_user,
    issue_token_pair,
    logout_tokens,
    refresh_access_token,
    register_user,
)

router = APIRouter()


@router.post('/register', response_model=TokenPair, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> TokenPair:
    user = register_user(db, payload)
    tokens = issue_token_pair(user, get_redis())
    return TokenPair(user=UserRead.model_validate(user), **tokens)


@router.post('/login', response_model=TokenPair)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> TokenPair:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='用户名或密码错误')

    tokens = issue_token_pair(user, get_redis())
    return TokenPair(user=UserRead.model_validate(user), **tokens)


@router.post('/refresh', response_model=TokenPair)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)) -> TokenPair:
    user, tokens = refresh_access_token(db, get_redis(), payload.refresh_token)
    return TokenPair(user=UserRead.model_validate(user), **tokens)


@router.post('/logout', response_model=MessageResponse)
def logout(
    payload: LogoutRequest,
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    logout_tokens(get_redis(), payload.access_token, payload.refresh_token)
    return MessageResponse(message=f'用户 {current_user.username} 已退出登录')


@router.get('/me', response_model=UserRead)
def me(current_user: User = Depends(get_current_user)) -> UserRead:
    return UserRead.model_validate(current_user)
