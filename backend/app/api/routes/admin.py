import logging
from typing import Annotated

from app.api.schemas.app_settings import AppSettingsRead, AppSettingsUpdate
from app.api.schemas.generic import SimpleResponseSchema
from app.api.utils.authentication import require_admin
from app.db.deps import get_db
from app.db.models import AppSettings, User
from fastapi import APIRouter, Depends, HTTPException, status
from fastcrud import FastCRUD
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.crud import get_app_settings

router = APIRouter(prefix="/admin", tags=["admin"])

app_settings_crud = FastCRUD(AppSettings)

logger = logging.getLogger(__name__)


@router.get(
    "/settings",
    summary="Get app settings (Admin only)",
    response_model=AppSettingsRead,
)
async def get_app_settings_endpoint(
    db: Annotated[AsyncSession, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin())],
) -> AppSettingsRead:
    """
    Get current app settings. Admin access required.
    """
    try:
        settings = await get_app_settings(db)
        return settings

    except Exception as e:
        logger.error(f"Failed to get app settings: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get app settings: {str(e)}",
        )


@router.patch(
    "/settings",
    summary="Update app settings (Admin only)",
    response_model=SimpleResponseSchema,
)
async def update_app_settings(
    settings_update: AppSettingsUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin_user: Annotated[User, Depends(require_admin())],
) -> SimpleResponseSchema:
    """
    Update app settings. Admin access required.
    """
    try:
        await app_settings_crud.update(db, id=1, object=settings_update.model_dump())

        await db.commit()

        return SimpleResponseSchema(message="App settings updated successfully")

    except Exception as e:
        logger.error(f"Failed to update app settings: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update app settings: {str(e)}",
        )
