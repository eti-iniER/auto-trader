from typing import Optional

from app.db.deps import get_db_context
from app.db.enums import LogType
from app.db.models import Instrument, Log, User, UserSettings
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload


async def log_message(
    message: str, description: str, log_type: LogType, extra: Optional[dict] = None
) -> Log:
    """
    Logs a message to the database.

    Args:
        message (str): The log message.
        log_type (LogType): The type of log.
        extra (Optional[dict]): Additional information to log.

    Returns:
        Log: The created log entry.
    """

    async with get_db_context() as db:
        log_entry = Log(
            message=message, description=description, type=log_type, extra=extra
        )
        db.add(log_entry)
        await db.commit()
        await db.refresh(log_entry)
        return log_entry


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """
    Retrieve a user by their ID.

    Args:
        db (AsyncSession): The database session.
        email (str): The email of the user to retrieve.
    Returns:
        User: The user object if found, otherwise raises an error.
    """
    stmt = select(User).options(selectinload(User.settings)).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    return user


async def get_user_by_refresh_token(
    db: AsyncSession, refresh_token: str
) -> User | None:
    """
    Retrieve a user by their refresh token.

    Args:
        db (AsyncSession): The database session.
        refresh_token (str): The refresh token of the user to retrieve.
    Returns:
        User: The user object if found, otherwise raises an error.
    """
    stmt = select(User).where(User.refresh_token == refresh_token)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    return user


async def update_user(db: AsyncSession, email: str, user_data: dict) -> User:
    """
    Update an existing user in the database.

    :param db: The database session.
    :param user_id: The ID of the user to update.
    :param user_data: A dictionary containing the updated user data.
    :return: The updated user object if found, otherwise None.
    """
    user = await get_user_by_email(db, email)

    for key, value in user_data.items():
        setattr(user, key, value)

    await db.commit()
    await db.refresh(user)
    return user


async def update_user_settings(
    db: AsyncSession, email: str, settings_data: dict
) -> User:
    """
    Update user settings in the database.
    :param db: The database session.
    :param email: The email of the user whose settings are to be updated.
    :param settings_data: A dictionary containing the updated settings data.
    :return: The updated user object with the new settings.
    """

    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{email}' not found.",
        )

    user_settings = user.settings or UserSettings(user_id=user.id)

    for key, value in settings_data.items():
        setattr(user_settings, key, value)

    user.settings = user_settings
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_instrument_by_ig_epic(db: AsyncSession, ig_epic: str) -> Instrument:
    """
    Retrieve an instrument by its IG epic.

    Args:
        db (AsyncSession): The database session.
        ig_epic (str): The IG epic of the instrument to retrieve.

    Returns:
        Instrument: The instrument object if found, otherwise None.
    """
    stmt = select(Instrument).where(Instrument.ig_epic == ig_epic)
    result = await db.execute(stmt)
    instrument = result.scalar_one_or_none()

    if not instrument:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument with IG epic '{ig_epic}' not found.",
        )

    return instrument


async def get_user_by_webhook_secret(db: AsyncSession, secret: str) -> User:
    """
    Retrieve a user by their webhook secret.

    Args:
        db (AsyncSession): The database session.
        secret (str): The webhook secret of the user to retrieve.

    Returns:
        User: The user object if found, otherwise None.
    """
    stmt = (
        select(User)
        .options(selectinload(User.settings))
        .where(
            (User.settings.has(UserSettings.demo_webhook_secret == secret))
            | (User.settings.has(UserSettings.live_webhook_secret == secret))
        )
    )
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with the provided webhook secret not found.",
        )
    return user


async def get_instrument_by_market_and_symbol(
    db: AsyncSession, market_and_symbol: str
) -> Instrument:
    """
    Retrieve an instrument by its market and symbol.

    Args:
        db (AsyncSession): The database session.
        market_and_symbol (str): The market and symbol of the instrument to retrieve.

    Returns:
        Instrument: The instrument object if found, otherwise raises an error.
    """
    stmt = select(Instrument).where(Instrument.market_and_symbol == market_and_symbol)
    result = await db.execute(stmt)
    instrument = result.scalar_one_or_none()

    if not instrument:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument with market and symbol '{market_and_symbol}' not found.",
        )

    return instrument
