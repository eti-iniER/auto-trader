from fastapi import Depends
from app.db.crud import get_app_settings as get_app_settings_crud
from app.db.deps import get_db
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession


async def get_app_settings(
    db: Annotated[AsyncSession, Depends(get_db)],
):
    settings = await get_app_settings_crud(db)
    return settings
