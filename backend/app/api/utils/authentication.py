import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

import jwt
from app.config import settings
from app.db.crud import get_user_by_email
from app.db.deps import get_db, get_db_context
from app.db.models import User
from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyCookie
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

password_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

access_token_cookie = APIKeyCookie(name="access_token", auto_error=False)
refresh_token_cookie = APIKeyCookie(name="refresh_token", auto_error=False)


class TokenData(BaseModel):
    email: str = Field(..., alias="sub")
    lifetime: int = Field(..., alias="exp")


async def get_access_token_from_cookie(
    token: Annotated[str, Depends(access_token_cookie)],
):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


async def get_refresh_token_from_cookie(
    token: Annotated[str, Depends(refresh_token_cookie)],
):
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return token


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: The plaintext password to hash.

    Returns:
        The hashed password.
    """
    return password_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against a hashed password.

    Args:
        plain_password: The plaintext password to verify.
        hashed_password: The hashed password to compare against.

    Returns:
        True if the passwords match, False otherwise.
    """
    return password_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            seconds=settings.ACCESS_TOKEN_LIFETIME_IN_SECONDS
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            seconds=settings.REFRESH_TOKEN_LIFETIME_IN_SECONDS
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


async def authenticate_user(db: AsyncSession, email: str, password: str):
    user = await get_user_by_email(db, email)

    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user


async def get_current_user(
    token: Annotated[str, Depends(get_access_token_from_cookie)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        token_data = TokenData(**payload)

        if not token_data.email:
            raise credentials_exception

    except jwt.InvalidTokenError:
        raise credentials_exception

    user = await get_user_by_email(db, token_data.email)

    if user is None:
        raise credentials_exception
    return user
