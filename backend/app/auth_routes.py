from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import (
    CurrentUser,
    create_session,
    password_hasher,
    validate_origin,
    verify_password,
)
from app.config import get_settings
from app.db import get_db
from app.models import User, UserSession
from app.schemas import LoginRequest, RegisterRequest, UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=201,
    dependencies=[Depends(validate_origin)],
)
def register(payload: RegisterRequest, response: Response, db: Annotated[Session, Depends(get_db)]):
    email = payload.email.lower().strip()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(status_code=409, detail="Unable to create account")
    user = User(
        email=email,
        display_name=payload.display_name.strip(),
        password_hash=password_hasher.hash(payload.password),
    )
    db.add(user)
    db.flush()
    token = create_session(db, user)
    db.commit()
    response.set_cookie(
        get_settings().session_cookie_name,
        token,
        httponly=True,
        secure=get_settings().cookie_secure,
        samesite="lax",
        max_age=get_settings().session_ttl_hours * 3600,
    )
    return user


@router.post("/login", response_model=UserResponse, dependencies=[Depends(validate_origin)])
def login(payload: LoginRequest, response: Response, db: Annotated[Session, Depends(get_db)]):
    user = db.scalar(select(User).where(User.email == payload.email.lower().strip()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_session(db, user)
    db.commit()
    response.set_cookie(
        get_settings().session_cookie_name,
        token,
        httponly=True,
        secure=get_settings().cookie_secure,
        samesite="lax",
        max_age=get_settings().session_ttl_hours * 3600,
    )
    return user


@router.post("/logout", status_code=204, dependencies=[Depends(validate_origin)])
def logout(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
    user: CurrentUser,
):
    token = request.cookies.get(get_settings().session_cookie_name)
    from app.auth import _hash_token

    session = db.scalar(select(UserSession).where(UserSession.token_hash == _hash_token(token)))
    if session:
        session.revoked_at = datetime.now(timezone.utc)
    db.commit()
    response.delete_cookie(get_settings().session_cookie_name)


@router.get("/me", response_model=UserResponse)
def me(user: CurrentUser):
    return user
