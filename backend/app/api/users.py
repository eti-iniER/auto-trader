import logging
from typing import Annotated

from app.api.schemas.generic import SimpleResponseSchema
from app.api.utils.authentication import (
    get_current_user,
    hash_password,
    verify_password,
)
from app.db.crud import update_user
from app.db.deps import get_db
from app.db.models import User, UserSettings
from app.schemas.user_settings import UserSettingsRead, UserSettingsUpdate
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from fastcrud import FastCRUD
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/users", tags=["users"])

user_settings_crud = FastCRUD(UserSettings)

logger = logging.getLogger(__name__)


class ChangePasswordPayload(BaseModel):
    new_password: str


@router.get(
    "/me/settings", response_model=UserSettingsRead, summary="Get user settings"
)
async def get_user_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> UserSettingsRead:
    """
    Get the current user's settings.
    """
    try:
        user_settings = await user_settings_crud.get(
            db, schema_to_select=UserSettingsRead, return_as_model=True, user_id=user.id
        )

        if not user_settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User settings not found",
            )

        return user_settings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to retrieve user settings for user {user.email}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user settings: {str(e)}",
        )


@router.patch(
    "/me/settings", response_model=UserSettingsRead, summary="Update user settings"
)
async def update_user_settings(
    settings_update: UserSettingsUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> UserSettingsRead:
    """
    Update the current user's settings.
    """
    try:
        existing_settings = await user_settings_crud.exists(db, user_id=user.id)
        if not existing_settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User settings not found",
            )

        update_data = settings_update.model_dump(exclude_unset=True, exclude_none=False)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid fields provided for update",
            )

        updated_settings = await user_settings_crud.update(
            db,
            update_data,
            schema_to_select=UserSettingsRead,
            return_as_model=True,
            user_id=user.id,
        )

        return updated_settings
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user settings for user {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user settings: {str(e)}",
        )


@router.patch(
    "/me/change-password",
    summary="Change user password",
    response_model=SimpleResponseSchema,
)
async def change_password(
    payload: ChangePasswordPayload,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
):
    """
    Change the current user's password.
    This endpoint is typically used after password reset token verification.
    """
    try:
        # Hash new password
        new_password_hash = hash_password(payload.new_password)

        # Update password in database
        await update_user(
            db, email=user.email, user_data={"password_hash": new_password_hash}
        )

        logger.info(f"Password changed successfully for user {user.email}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "Password changed successfully."},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to change password for user {user.email}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}",
        )
