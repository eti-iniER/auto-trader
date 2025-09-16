import logging
import uuid
from typing import Annotated

from app.api.exceptions import APIException
from app.api.schemas.generic import SimpleResponseSchema
from app.api.schemas.user import UserAdminSchema, UserUpdateSchema
from app.api.schemas.user_settings import UserSettingsRead, UserSettingsUpdate
from app.api.utils.authentication import get_current_user, hash_password, require_admin
from app.api.utils.pagination import (
    PaginatedResponse,
    PaginationParams,
    build_paginated_response,
)
from app.clients.ig import IGClient
from app.db.models import AppSettings
from app.api.utils.admin import get_app_settings
from app.db.crud import update_user
from app.db.deps import get_db
from app.db.models import User, UserSettings
from app.services.logging import log_message
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

        IGClient.invalidate_user_cache(user)
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
    "",
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
    user_id: uuid.UUID,
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


@router.patch(
    "/{user_id}",
    summary="Update user by ID (Admin only)",
    response_model=SimpleResponseSchema,
)
async def update_user_endpoint(
    user_id: uuid.UUID,
    user_update: UserUpdateSchema,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin())],
    app_settings: Annotated[AppSettings, Depends(get_app_settings)],
) -> SimpleResponseSchema:
    """
    Update a specific user by ID. Admin access required.
    """
    try:
        existing_user: UserAdminSchema = await user_crud.get(
            db, id=user_id, return_as_model=True, schema_to_select=UserAdminSchema
        )
        if not existing_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        update_data = user_update.model_dump(exclude_unset=True, exclude_none=True)

        if update_data.get("role"):
            if admin_user.id == user_id and update_data["role"] == "USER":
                raise APIException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    message="You cannot disable your own admin permissions",
                    code="CANNOT_UNMAKE_ADMIN",
                )

            if (
                app_settings.allow_multiple_admins is False
                and update_data["role"] == "ADMIN"
            ):
                admin_count = await user_crud.count(db, role="ADMIN")
                if admin_count >= 1 and existing_user.role != "ADMIN":
                    raise APIException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        message="Multiple admins are not allowed by current app settings",
                        code="MULTIPLE_ADMINS_NOT_ALLOWED",
                    )

        await user_crud.update(
            db,
            update_data,
            schema_to_select=UserAdminSchema,
            return_as_model=True,
            id=user_id,
        )

        return SimpleResponseSchema(message="User updated successfully.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update user {user_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}",
        )


@router.delete(
    "/{user_id}",
    summary="Delete user by ID (Admin only)",
    response_model=SimpleResponseSchema,
)
async def delete_user(
    user_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin())],
):
    """
    Delete a specific user by ID. Admin access required.
    Cannot delete yourself.
    """
    try:
        # Check if user exists
        user_to_delete: UserAdminSchema = await user_crud.get(
            db, id=user_id, return_as_model=True, schema_to_select=UserAdminSchema
        )

        if not user_to_delete:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                message="User not found",
                code="USER_NOT_FOUND",
            )

        # Prevent admin from deleting themselves
        if admin_user.id == user_id:
            raise APIException(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="You cannot delete yourself",
                code="CANNOT_DELETE_SELF",
            )

        # Delete the user
        await user_crud.delete(db, id=user_id)

        await log_message(
            message="User deleted",
            description=f"You deleted user {user_to_delete.first_name} {user_to_delete.last_name} ({user_to_delete.email})",
            log_type="admin",
            user_id=admin_user.id,
            extra={
                "deleted_user_data": user_to_delete.model_dump(
                    mode="json", exclude={"password_hash", "refresh_token"}
                ),
            },
        )

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
