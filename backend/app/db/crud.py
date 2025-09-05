import uuid
from typing import Optional

from app.db.deps import get_db_context
from app.db.enums import LogType, UserRole
from app.db.models import Instrument, Log, Order, User, UserSettings, AppSettings
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload


async def get_market_and_symbol_by_ig_epic(
    db: AsyncSession, user_id: str, ig_epic: str
) -> Optional[str]:
    """
    Get market_and_symbol for a given ig_epic from user's instruments.

    Args:
        db: Database session
        user_id: User ID
        ig_epic: IG epic to search for

    Returns:
        market_and_symbol if found, None otherwise
    """
    stmt = select(Instrument).where(
        Instrument.user_id == user_id, Instrument.ig_epic == ig_epic
    )
    result = await db.execute(stmt)
    instrument = result.scalar_one_or_none()

    return instrument.market_and_symbol if instrument else None


async def log_message(
    message: str,
    description: Optional[str],
    log_type: LogType,
    user_id: uuid.UUID,
    extra: Optional[dict] = None,
    identifier: Optional[str] = None,
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
            message=message,
            description=description,
            type=log_type,
            extra=extra,
            user_id=user_id,
            identifier=identifier,
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


async def get_user_by_webhook_secret(db: AsyncSession, secret: str) -> Optional[User]:
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

    return user


async def get_instrument_by_market_and_symbol(
    db: AsyncSession, market_and_symbol: str, user: User
) -> Optional[Instrument]:
    """
    Retrieve an instrument by its market and symbol.

    Args:
        db (AsyncSession): The database session.
        market_and_symbol (str): The market and symbol of the instrument to retrieve.

    Returns:
        Instrument: The instrument object if found, otherwise raises an error.
    """
    stmt = select(Instrument).where(
        Instrument.market_and_symbol == market_and_symbol, Instrument.user_id == user.id
    )
    result = await db.execute(stmt)
    instrument = result.scalar_one_or_none()

    return instrument


async def create_order_for_instrument(
    db: AsyncSession, instrument: Instrument
) -> Order:
    """
    Create an order for a given instrument.

    Args:
        db (AsyncSession): The database session.
        instrument_id (uuid.UUID): The ID of the instrument to create an order for.

    Returns:
        Order: The created order object.
    """

    order = Order(instrument_id=instrument.id, user_id=instrument.user_id)
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


async def delete_order(db: AsyncSession, order_id: uuid.UUID) -> None:
    """
    Delete an order by its ID.

    Args:
        db (AsyncSession): The database session.
        order_id (uuid.UUID): The ID of the order to delete.

    Returns:
        None
    """
    stmt = select(Order).where(Order.id == order_id)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID '{order_id}' not found.",
        )

    await db.delete(order)
    await db.commit()


async def update_order(
    db: AsyncSession, order_id: uuid.UUID, update_data: dict
) -> Order:
    """
    Update an order by its ID.

    Args:
        db (AsyncSession): The database session.
        order_id (uuid.UUID): The ID of the order to update.
        update_data (dict): Dictionary of fields to update.

    Returns:
        Order: The updated order object.
    """
    stmt = select(Order).where(Order.id == order_id)
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID '{order_id}' not found.",
        )

    # Update the order with the provided data
    for key, value in update_data.items():
        if hasattr(order, key):
            setattr(order, key, value)

    await db.commit()
    await db.refresh(order)
    return order


async def get_order_by_id(db: AsyncSession, order_id: uuid.UUID) -> Order:
    """
    Retrieve an order by its ID.

    Args:
        db (AsyncSession): The database session.
        order_id (uuid.UUID): The ID of the order to retrieve.

    Returns:
        Order: The order object if found, otherwise raises an error.
    """
    stmt = (
        select(Order)
        .options(
            selectinload(Order.instrument)
            .selectinload(Instrument.user)
            .selectinload(User.settings)
        )
        .where(Order.id == order_id)
    )
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID '{order_id}' not found.",
        )

    return order


async def get_order_by_deal_id(db: AsyncSession, deal_id: str) -> Order:
    """
    Retrieve an order by its IG deal ID.

    Args:
        db (AsyncSession): The database session.
        deal_id (str): The IG deal ID of the order to retrieve.

    Returns:
        Order: The order object if found, otherwise raises an error.
    """
    stmt = (
        select(Order)
        .options(
            selectinload(Order.instrument)
            .selectinload(Instrument.user)
            .selectinload(User.settings)
        )
        .where(Order.deal_id == deal_id)
    )
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with deal ID '{deal_id}' not found.",
        )

    return order


async def get_app_settings(db: AsyncSession) -> AppSettings:
    """
    Retrieve the application settings.

    Args:
        db (AsyncSession): The database session.

    Returns:
        AppSettings: The application settings object.
    """
    stmt = select(AppSettings).where(AppSettings.id == 1)
    result = await db.execute(stmt)
    app_settings = result.scalar_one_or_none()

    if not app_settings:
        app_settings = AppSettings()
        db.add(app_settings)
        await db.commit()
        await db.refresh(app_settings)

    return app_settings


async def universal_search_instruments(
    db: AsyncSession,
    user_id: uuid.UUID,
    query: str,
    offset: int = 0,
    limit: int = 100,
) -> dict:
    """
    Search instruments across multiple fields (market_and_symbol, ig_epic, yahoo_symbol).

    Args:
        db: Database session
        user_id: User ID to filter by
        query: Search query string
        offset: Pagination offset
        limit: Pagination limit

    Returns:
        Dict with 'data' (list of instruments) and 'total_count'
    """
    from sqlalchemy import or_, func

    # Build the base query
    search_query = (
        select(Instrument)
        .where(Instrument.user_id == user_id)
        .where(
            or_(
                func.lower(Instrument.market_and_symbol).contains(func.lower(query)),
                func.lower(Instrument.ig_epic).contains(func.lower(query)),
                func.lower(Instrument.yahoo_symbol).contains(func.lower(query)),
            )
        )
        .order_by(Instrument.updated_at.desc())
    )

    # Get total count
    count_query = select(func.count()).select_from(
        select(Instrument)
        .where(Instrument.user_id == user_id)
        .where(
            or_(
                func.lower(Instrument.market_and_symbol).contains(func.lower(query)),
                func.lower(Instrument.ig_epic).contains(func.lower(query)),
                func.lower(Instrument.yahoo_symbol).contains(func.lower(query)),
            )
        )
        .subquery()
    )

    total_result = await db.execute(count_query)
    total_count = total_result.scalar()

    # Apply pagination
    search_query = search_query.offset(offset).limit(limit)

    # Execute query
    result = await db.execute(search_query)
    instruments = result.scalars().all()

    return {
        "data": instruments,
        "total_count": total_count,
    }


async def get_most_recent_order_for_instrument(
    db: AsyncSession, instrument_id: uuid.UUID
) -> Optional[Order]:
    """
    Retrieve the most recent order for a given instrument.

    Args:
        db (AsyncSession): The database session.
        instrument_id (uuid.UUID): The ID of the instrument.

    Returns:
        Order: The most recent order object if found, otherwise None.
    """
    stmt = (
        select(Order)
        .where(Order.instrument_id == instrument_id)
        .order_by(Order.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    return order


async def get_open_orders_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[Order]:
    """
    Retrieve all open orders for a given user.

    Args:
        db (AsyncSession): The database session.
        user_id (uuid.UUID): The ID of the user.

    Returns:
        List[Order]: A list of open order objects.
    """
    stmt = select(Order).where(Order.user_id == user_id, Order.is_open == True)
    result = await db.execute(stmt)
    orders = result.scalars().all()

    return orders


async def get_orders_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[Order]:
    """
    Retrieve all orders for a given user.

    Args:
        db (AsyncSession): The database session.
        user_id (uuid.UUID): The ID of the user.

    Returns:
        List[Order]: A list of order objects.
    """
    stmt = select(Order).where(Order.user_id == user_id)
    result = await db.execute(stmt)
    orders = result.scalars().all()

    return orders


async def get_all_orders_with_deal_id(db: AsyncSession) -> list[Order]:
    """
    Retrieve all orders that have a deal_id assigned.

    Args:
        db (AsyncSession): The database session.

    Returns:
        List[Order]: A list of order objects with deal_id.
    """
    stmt = (
        select(Order)
        .options(selectinload(Order.user).selectinload(User.settings))
        .options(selectinload(Order.instrument))
        .where(Order.deal_id.is_not(None))
    )
    result = await db.execute(stmt)
    orders = result.scalars().all()

    return orders


async def get_all_admin_users(db: AsyncSession) -> list[User]:
    """
    Retrieve all users with admin privileges.

    Args:
        db (AsyncSession): The database session.

    Returns:
        List[User]: A list of admin user objects.
    """
    stmt = select(User).where(User.role == UserRole.ADMIN)
    result = await db.execute(stmt)
    users = result.scalars().all()

    return users
