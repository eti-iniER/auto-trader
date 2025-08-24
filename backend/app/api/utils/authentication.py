import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated, List, Optional

import jwt
from app.config import settings
from app.db.crud import get_user_by_email
from app.db.deps import get_db, get_db_context
from app.db.enums import UserRole
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


def require_role(allowed_roles: List[UserRole]):
    """
    Dependency factory to require specific user roles.

    Args:
        allowed_roles: List of UserRole enums that are allowed to access the endpoint

    Returns:
        FastAPI dependency function that checks user role

    Raises:
        HTTPException: 403 if user doesn't have required role
    """

    def role_checker(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[role.value for role in allowed_roles]}",
            )
        return user

    return role_checker


def require_admin():
    """
    Convenience dependency for admin-only routes.

    Returns:
        FastAPI dependency function that checks for admin role

    Raises:
        HTTPException: 403 if user is not an admin
    """
    return require_role([UserRole.ADMIN])


def create_password_reset_token(
    email: str, expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a signed JWT token for password reset.

    Args:
        email: User email address
        expires_delta: Token expiration time (defaults to 1 hour)

    Returns:
        Signed JWT token
    """
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)

    to_encode = {"sub": email, "exp": expire, "purpose": "password_reset"}

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


async def verify_password_reset_token(token: str) -> User:
    """
    Verify and decode a password reset token.

    Args:
        token: JWT token to verify

    Returns:
        User object if token is valid

    Raises:
        HTTPException: If token is invalid or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired reset token",
    )

    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )

        email: str = payload.get("sub")
        purpose: str = payload.get("purpose")

        if email is None or purpose != "password_reset":
            raise credentials_exception

    except jwt.InvalidTokenError:
        raise credentials_exception

    async with get_db_context() as db:
        user = await get_user_by_email(db, email)
        if user is None:
            raise credentials_exception

    return user


def generate_reset_link(token: str, origin: str) -> str:
    """
    Generate a password reset link with the token.

    Args:
        token: Password reset token
        origin: The origin URL from the request

    Returns:
        Complete reset link URL
    """
    return f"{origin}/auth/change-password?token={token}"
