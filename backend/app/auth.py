import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Annotated

from argon2 import PasswordHasher
from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.models import User, UserSession

password_hasher = PasswordHasher()


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except Exception:
        return False


def create_session(db: Session, user: User) -> str:
    token = secrets.token_urlsafe(32)
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=_hash_token(token),
            expires_at=datetime.now(timezone.utc)
            + timedelta(hours=get_settings().session_ttl_hours),
        )
    )
    return token


def get_current_user(request: Request, db: Annotated[Session, Depends(get_db)]) -> User:
    token = request.cookies.get(get_settings().session_cookie_name)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )
    session = db.scalar(
        select(UserSession).where(
            UserSession.token_hash == _hash_token(token),
            UserSession.expires_at > datetime.now(timezone.utc),
            UserSession.revoked_at.is_(None),
        )
    )
    if session is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    user = db.get(User, session.user_id)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Authentication required")
    session.last_used_at = datetime.now(timezone.utc)
    db.commit()
    return user


def validate_origin(request: Request) -> None:
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return
    origin = request.headers.get("origin")
    trusted = {
        item.strip().rstrip("/")
        for item in get_settings().trusted_origins.split(",")
        if item.strip()
    }
    if not origin or origin.rstrip("/") not in trusted:
        raise HTTPException(status_code=403, detail="Invalid request origin")


CurrentUser = Annotated[User, Depends(get_current_user)]
