"""Create tables and optional bootstrap admin."""

from sqlalchemy.orm import Session

from app.config import Settings
from app.models import User
from app.security import hash_password


def ensure_admin(settings: Settings, db: Session) -> None:
    if not settings.bootstrap_admin_email or not settings.bootstrap_admin_password:
        return
    exists = db.query(User).filter(User.email == settings.bootstrap_admin_email).first()
    if exists:
        return
    db.add(
        User(
            email=settings.bootstrap_admin_email,
            hashed_password=hash_password(settings.bootstrap_admin_password),
            is_admin=True,
        )
    )
    db.commit()
