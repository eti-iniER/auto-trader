import logging
from typing import Annotated

from app.api.schemas.generic import SimpleResponseSchema
from app.api.schemas.user import UserAdminSchema
from app.api.schemas.user_settings import UserSettingsRead, UserSettingsUpdate
from app.api.utils.authentication import get_current_user, hash_password, require_admin
from app.api.utils.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
)
from app.db.crud import update_user
from app.db.deps import get_db
from app.db.models import User, UserSettings
from app.services.utils import generate_webhook_secret
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastcrud import FastCRUD
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/users", tags=["users"])

user_settings_crud = FastCRUD(UserSettings)
user_crud = FastCRUD(User)

logger = logging.getLogger(__name__)


class ChangePasswordPayload(BaseModel):
    new_password: str


class NewWebhookSecretResponse(BaseModel):
    secret: str


@router.get(
    "/me/settings/new-webhook-secret",
    summary="Generate a new webhook secret",
    response_model=NewWebhookSecretResponse,
)
async def new_webhook_secret(
    user: Annotated[User, Depends(get_current_user)],
) -> NewWebhookSecretResponse:
    """
    Generate and return a new webhook secret.
    """
    try:
        new_webhook_secret = generate_webhook_secret()

        logger.info(f"New webhook secret generated for user {user.email}")

        return NewWebhookSecretResponse(secret=new_webhook_secret)
    except Exception as e:
        logger.error(
            f"Failed to generate webhook secret for user {user.email}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate webhook secret: {str(e)}",
        )


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


# Admin-only endpoints for user management
@router.get(
    "/",
    summary="List all users (Admin only)",
    response_model=PaginatedResponse[UserAdminSchema],
)
async def list_users(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin())],
    pagination: Annotated[PaginationParams, Depends()],
) -> PaginatedResponse[UserAdminSchema]:
    """
    List all users with pagination. Admin access required.
    """
    try:
        result = await user_crud.get_multi(
            db,
            offset=pagination.offset,
            limit=pagination.limit,
            schema_to_select=UserAdminSchema,
            return_as_model=True,
            sort_columns=["last_login"],
            sort_orders=["desc"],
        )

        return build_paginated_response(
            request=request,
            result=result,
            offset=pagination.offset,
            limit=pagination.limit,
            endpoint="/api/v1/users/",
            response_class=UserAdminSchema,
        )
    except Exception as e:
        logger.error(f"Failed to retrieve users list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve users: {str(e)}",
        )


@router.get(
    "/{user_id}",
    summary="Get user by ID (Admin only)",
    response_model=UserAdminSchema,
)
async def get_user(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin())],
) -> UserAdminSchema:
    """
    Get a specific user by ID. Admin access required.
    """
    try:
        user = await user_crud.get(
            db,
            schema_to_select=UserAdminSchema,
            return_as_model=True,
            id=user_id,
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve user: {str(e)}",
        )


@router.delete(
    "/{user_id}",
    summary="Delete user by ID (Admin only)",
    response_model=SimpleResponseSchema,
)
async def delete_user(
    user_id: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin())],
):
    """
    Delete a specific user by ID. Admin access required.
    Cannot delete yourself.
    """
    try:
        # Check if user exists
        user_to_delete = await user_crud.get(db, id=user_id)
        if not user_to_delete:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Prevent admin from deleting themselves
        if str(admin_user.id) == user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete your own account",
            )

        # Delete the user
        await user_crud.delete(db, id=user_id)

        logger.info(f"User {user_id} deleted by admin {admin_user.email}")

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "User deleted successfully."},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}",
        )
