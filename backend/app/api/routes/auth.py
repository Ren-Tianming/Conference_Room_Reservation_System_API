from __future__ import annotations

from typing import Optional, Union

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.api.deps import bearer_scheme, get_current_user, get_db
from app.models.user import User
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshRequest, TokenResponse
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import (
    SessionMetadata,
    authenticate_user,
    create_access_and_refresh_tokens,
    register_user,
    revoke_all_tokens,
    revoke_tokens,
    rotate_refresh_token,
)

router = APIRouter()


@router.post('/register', response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> UserRead:
    user = register_user(db, payload)
    return UserRead.model_validate(user)


def _session_metadata(request: Request) -> SessionMetadata:
    user_agent = request.headers.get('user-agent')
    return SessionMetadata(
        user_agent=user_agent[:255] if user_agent else None,
        ip_address=request.client.host[:45] if request.client else None,
        device_name=request.headers.get('x-device-name', '')[:100] or None,
    )


@router.post('/login', response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    user = authenticate_user(db, payload.username, payload.password)
    return create_access_and_refresh_tokens(db, user, _session_metadata(request))


@router.post('/refresh', response_model=TokenResponse)
def refresh_token(payload: RefreshRequest, request: Request, db: Session = Depends(get_db)) -> TokenResponse:
    return rotate_refresh_token(db, payload.refresh_token, _session_metadata(request))


@router.post('/logout', status_code=status.HTTP_200_OK)
def logout(
    payload: LogoutRequest,
    current_user: User = Depends(get_current_user),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    assert credentials is not None
    revoke_tokens(db, access_token=credentials.credentials, refresh_token=payload.refresh_token, user_id=current_user.id)
    return {"message": "ログアウトしました。"}


@router.post('/logout-all', status_code=status.HTTP_200_OK)
def logout_all(
    current_user: User = Depends(get_current_user),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> dict[str, Union[int, str]]:
    assert credentials is not None
    revoked_sessions = revoke_all_tokens(db, access_token=credentials.credentials, user_id=current_user.id)
    return {"message": "全ての端末からログアウトしました。", "revoked_sessions": revoked_sessions}
