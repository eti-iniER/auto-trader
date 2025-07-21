from app.db.session import async_session
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session() as session:
        yield session


@asynccontextmanager
async def get_db_context():
    async with async_session() as session:
        yield session
