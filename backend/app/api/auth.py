import logging
from datetime import timedelta
from typing import Annotated

from app.api.schemas.generic import SimpleResponseSchema
from app.api.schemas.user import UserSchema
from app.config import settings
from app.db.crud import get_user_by_email, get_user_by_refresh_token, update_user
from app.db.deps import get_db
from app.db.models import User, UserSettings
from fastapi import APIRouter, Depends, Response, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from .utils.authentication import (
    authenticate_user,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_refresh_token_from_cookie,
    hash_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])

logger = logging.getLogger(__name__)


class OAuthPayload(BaseModel):
    code: str
    state: str | None = None


class AdminLoginPayload(BaseModel):
    email: EmailStr


class LoginPayload(BaseModel):
    email: EmailStr
    password: str


class RegisterPayload(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str


class ResetPasswordPayload(BaseModel):
    email: EmailStr


@router.post("/register", response_model=UserSchema, summary="User registration")
async def register_user(
    payload: RegisterPayload,
    db: Annotated[AsyncSession, Depends(get_db)],
    response: Response,
) -> UserSchema:
    """
    Endpoint for user registration.
    """
    existing_user = await get_user_by_email(db, payload.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed_password = hash_password(payload.password)
    new_user = User(
        email=payload.email,
        password_hash=hashed_password,
        first_name=payload.first_name,
        last_name=payload.last_name,
    )

    db.add(new_user)

    await db.commit()
    await db.refresh(new_user)

    new_user_settings = UserSettings(user_id=new_user.id)

    db.add(new_user_settings)
    await db.commit()

    access_token = create_access_token(
        data={"sub": new_user.email},
        expires_delta=timedelta(seconds=settings.ACCESS_TOKEN_LIFETIME_IN_SECONDS),
    )
    refresh_token = create_refresh_token(
        data={"sub": new_user.email},
        expires_delta=timedelta(seconds=settings.REFRESH_TOKEN_LIFETIME_IN_SECONDS),
    )
    await update_user(
        db, email=new_user.email, user_data={"refresh_token": refresh_token}
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="None",
        secure=True,
        max_age=settings.ACCESS_TOKEN_LIFETIME_IN_SECONDS,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="None",
        secure=True,
        max_age=settings.REFRESH_TOKEN_LIFETIME_IN_SECONDS,
    )
    return new_user


@router.post("/login", response_model=UserSchema, summary="User login")
async def login(
    response: Response,
    payload: LoginPayload,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserSchema:
    user = await authenticate_user(db, email=payload.email, password=payload.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(seconds=settings.ACCESS_TOKEN_LIFETIME_IN_SECONDS),
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email},
        expires_delta=timedelta(seconds=settings.REFRESH_TOKEN_LIFETIME_IN_SECONDS),
    )
    await update_user(db, email=user.email, user_data={"refresh_token": refresh_token})

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="None",
        secure=True,
        max_age=settings.ACCESS_TOKEN_LIFETIME_IN_SECONDS,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="None",
        secure=True,
        max_age=settings.REFRESH_TOKEN_LIFETIME_IN_SECONDS,
    )
    return user


@router.post(
    "/reset-password",
    summary="Send reset password email",
    response_model=SimpleResponseSchema,
)
async def send_reset_password_email(
    payload: ResetPasswordPayload, db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Endpoint to send a reset password email to the user.
    """
    user = await get_user_by_email(db, payload.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Here you would typically send an email with a reset link
    # For simplicity, we will just log the action
    logger.info(f"Reset password email sent to {payload.email}")

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "Reset password email sent successfully."},
    )


@router.post("/token", summary="Generate access token")
async def generate_access_token(
    token: Annotated[str, Depends(get_refresh_token_from_cookie)],
    db: Annotated[AsyncSession, Depends(get_db)],
    response: Response,
):
    """
    Endpoint to generate an access token for the authenticated user.
    This can be used to authenticate subsequent requests.
    """

    user = await get_user_by_refresh_token(db, token)

    if not user:
        response.delete_cookie("refresh_token")

        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": "Invalid refresh token."},
        )

    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(seconds=settings.ACCESS_TOKEN_LIFETIME_IN_SECONDS),
    )
    refresh_token = create_refresh_token(
        data={"sub": user.email},
        expires_delta=timedelta(seconds=settings.REFRESH_TOKEN_LIFETIME_IN_SECONDS),
    )

    await update_user(db, email=user.email, user_data={"refresh_token": refresh_token})

    response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": "Access token generated successfully.",
        },
    )

    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        samesite="None",
        secure=True,
        max_age=settings.ACCESS_TOKEN_LIFETIME_IN_SECONDS,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="None",
        secure=True,
        max_age=settings.REFRESH_TOKEN_LIFETIME_IN_SECONDS,
    )

    return response


@router.get("/me", response_model=UserSchema, summary="Get current user")
async def get_current_user_endpoint(
    user: Annotated[User, Depends(get_current_user)],
):
    """
    Endpoint to get the current authenticated user.
    This uses the access token from the cookie to identify the user.
    """
    return user


@router.post("/logout", summary="User logout")
async def logout(
    response: Response,
):
    """
    Endpoint to log out the user by clearing the access and refresh tokens.
    """
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "User logged out successfully."},
    )
