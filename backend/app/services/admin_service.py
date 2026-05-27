from __future__ import annotations

import logging

from sqlalchemy import select

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)


def seed_bootstrap_admin() -> None:
    """Create an optional initial admin user from environment variables."""
    if not settings.bootstrap_admin_username or not settings.bootstrap_admin_password:
        return

    db = SessionLocal()
    try:
        existing = db.execute(select(User).where(User.username == settings.bootstrap_admin_username)).scalar_one_or_none()
        if existing is not None:
            if existing.role != UserRole.ADMIN.value:
                existing.role = UserRole.ADMIN.value
                db.add(existing)
                db.commit()
            return

        admin = User(
            username=settings.bootstrap_admin_username,
            password_hash=get_password_hash(settings.bootstrap_admin_password),
            role=UserRole.ADMIN.value,
        )
        db.add(admin)
        db.commit()
        logger.info(
            'Bootstrap administrator created.',
            extra={'event': 'bootstrap_admin_created', 'user_id': admin.id, 'username': admin.username},
        )
    finally:
        db.close()
