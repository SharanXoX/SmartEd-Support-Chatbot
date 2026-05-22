"""Authentication endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.schemas import AdminLogin, Token
from app.security import create_access_token, hash_password, verify_password
from app.config import Settings, get_settings

router = APIRouter(prefix="/auth", tags=["auth"])


def _issue_token(email: str, settings: Settings) -> Token:
    return Token(access_token=create_access_token(email, settings))


@router.post("/token", response_model=Token)
def login_form(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Token:
    """OAuth2-compatible login (username field carries email)."""

    user = db.query(User).filter(User.email == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials")
    return _issue_token(user.email, settings)


@router.post("/login", response_model=Token)
def login_json(
    body: AdminLogin,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Token:
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Bad credentials")
    return _issue_token(user.email, settings)


@router.post("/bootstrap-first-admin", response_model=Token, status_code=status.HTTP_201_CREATED)
def bootstrap_first_admin(
    body: AdminLogin,
    db: Annotated[Session, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> Token:
    """Creates the first admin if no users exist (development convenience)."""

    existing = db.query(User).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bootstrap disabled")
    user = User(email=body.email, hashed_password=hash_password(body.password), is_admin=True)
    db.add(user)
    db.commit()
    return _issue_token(user.email, settings)
