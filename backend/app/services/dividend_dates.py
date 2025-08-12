import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict
from collections import defaultdict

from sqlalchemy import select, update, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.yahoo.client import YahooFinanceClient
from app.db.models import Instrument
from app.services.logging.helper import log_message

logger = logging.getLogger(__name__)


async def fetch_dividend_date_for_symbol(
    yahoo_client: YahooFinanceClient, symbol: str, instrument_id: uuid.UUID
) -> Tuple[uuid.UUID, Optional[datetime]]:
    """
    Fetch dividend date for a single symbol.

    Args:
        yahoo_client: YahooFinanceClient instance
        symbol: Yahoo symbol to fetch dividend date for
        instrument_id: Database ID of the instrument

    Returns:
        Tuple of (instrument_id, dividend_date)
    """
    try:
        dividend_datetime = yahoo_client.get_next_dividend_date(symbol)
        # Ensure the datetime is timezone-aware, defaulting to UTC if naive
        if dividend_datetime and dividend_datetime.tzinfo is None:
            dividend_datetime = dividend_datetime.replace(tzinfo=timezone.utc)
        logger.info(f"Fetched dividend date for {symbol}: {dividend_datetime}")
        return instrument_id, dividend_datetime
    except Exception as e:
        logger.error(f"Failed to fetch dividend date for symbol {symbol}: {str(e)}")
        return instrument_id, None


async def bulk_update_dividend_dates(
    db: AsyncSession, updates: List[Tuple[uuid.UUID, Optional[datetime]]]
) -> int:
    """
    Efficiently bulk update dividend dates using individual update statements.

    Args:
        session: Database session
        updates: List of (instrument_id, dividend_datetime) tuples

    Returns:
        Number of records updated
    """
    if not updates:
        return 0

    # Filter out None values and prepare for bulk update
    valid_updates = [
        (instrument_id, dividend_datetime)
        for instrument_id, dividend_datetime in updates
        if dividend_datetime is not None
    ]

    if not valid_updates:
        logger.info("No valid dividend dates to update")
        return 0

    try:
        updated_count = 0

        # Process updates in batches for better performance
        batch_size = 50
        for i in range(0, len(valid_updates), batch_size):
            batch = valid_updates[i : i + batch_size]

            # Create a batch update using SQLAlchemy's update with case statement
            when_clauses = []
            instrument_ids = []

            for instrument_id, dividend_datetime in batch:
                when_clauses.append((instrument_id, dividend_datetime))
                instrument_ids.append(instrument_id)

            if when_clauses:
                # Create case statement for the update
                case_stmt = case(
                    *[
                        (Instrument.id == instrument_id, dividend_datetime)
                        for instrument_id, dividend_datetime in when_clauses
                    ],
                    else_=Instrument.next_dividend_date,
                )

                stmt = (
                    update(Instrument)
                    .where(Instrument.id.in_(instrument_ids))
                    .values(next_dividend_date=case_stmt)
                )

                result = await db.execute(stmt)
                updated_count += result.rowcount

        await db.commit()
        logger.info(f"Updated dividend dates for {updated_count} instruments")
        return updated_count

    except Exception as e:
        logger.error(f"Error in bulk update: {str(e)}")
        await db.rollback()
        raise


async def fetch_and_update_all_dividend_dates(db: AsyncSession) -> int:
    """
    Fetch and update dividend dates for all instruments with Yahoo symbols.
    Uses parallel processing for efficient data fetching.
    Logs the update action per user when updating their instruments.

    Args:
        session: Database session

    Returns:
        Number of instruments updated
    """
    logger.info("Starting dividend dates update for all instruments")

    yahoo_client = YahooFinanceClient()

    # Fetch all instruments that have Yahoo symbols, including user_id and market_and_symbol for logging
    stmt = select(
        Instrument.id,
        Instrument.yahoo_symbol,
        Instrument.user_id,
        Instrument.market_and_symbol,
    ).where(Instrument.yahoo_symbol.isnot(None), Instrument.yahoo_symbol != "")
    result = await db.execute(stmt)
    instruments = result.all()

    if not instruments:
        logger.info("No instruments with Yahoo symbols found")
        return 0

    logger.info(f"Found {len(instruments)} instruments with Yahoo symbols")

    # Create tasks for parallel execution
    tasks = [
        fetch_dividend_date_for_symbol(
            yahoo_client, instrument.yahoo_symbol, instrument.id
        )
        for instrument in instruments
    ]

    # Execute all tasks in parallel with a reasonable concurrency limit
    # YFinance has rate limiting, so we'll batch the requests
    batch_size = 10  # Process 10 symbols concurrently
    updates = []

    for i in range(0, len(tasks), batch_size):
        batch = tasks[i : i + batch_size]
        batch_results = await asyncio.gather(*batch, return_exceptions=True)

        # Process results and filter out exceptions
        for result in batch_results:
            if isinstance(result, Exception):
                logger.error(f"Task failed with exception: {result}")
            else:
                updates.append(result)

        # Small delay between batches to be respectful to Yahoo Finance
        if i + batch_size < len(tasks):
            await asyncio.sleep(1)

    logger.info(f"Completed fetching dividend dates. Got {len(updates)} results")

    # Group instruments by user for logging purposes
    instrument_user_map = {
        instrument.id: instrument.user_id for instrument in instruments
    }
    instrument_market_symbol_map = {
        instrument.id: instrument.market_and_symbol for instrument in instruments
    }

    # Filter updates to only include successful ones
    successful_updates = [
        (instrument_id, dividend_datetime)
        for instrument_id, dividend_datetime in updates
        if dividend_datetime is not None
    ]

    # Group successful updates by user
    user_updates = defaultdict(list)
    for instrument_id, dividend_datetime in successful_updates:
        user_id = instrument_user_map.get(instrument_id)
        market_symbol = instrument_market_symbol_map.get(instrument_id)
        if user_id and market_symbol:
            user_updates[user_id].append(
                (instrument_id, dividend_datetime, market_symbol)
            )

    # Bulk update the database
    updated_count = await bulk_update_dividend_dates(db, updates)

    # Log the action for each user
    for user_id, user_update_list in user_updates.items():
        updated_instruments_count = len(user_update_list)
        await log_message(
            message=f"Dividend dates updated for {updated_instruments_count} instruments",
            description=f"Updated dividend dates for your instruments. {updated_instruments_count} instruments had their dividend dates refreshed from Yahoo Finance.",
            log_type="unspecified",
            user_id=user_id,
            extra={
                "action": "dividend_dates_update",
                "instruments_updated": updated_instruments_count,
                "updated_instruments": [
                    market_symbol for _, _, market_symbol in user_update_list
                ],
            },
        )
        logger.info(
            f"Logged dividend date update for user {user_id}: {updated_instruments_count} instruments"
        )

    logger.info(f"Successfully updated dividend dates for {updated_count} instruments")

    return updated_count


async def fetch_and_update_single_dividend_date(
    session: AsyncSession, instrument_id: uuid.UUID
) -> bool:
    """
    Fetch and update dividend date for a single instrument.
    Logs the update action for the user who owns the instrument.

    Args:
        session: Database session
        instrument_id: UUID of the instrument to update

    Returns:
        True if successfully updated, False otherwise
    """
    logger.info(f"Starting dividend date update for instrument {instrument_id}")

    yahoo_client = YahooFinanceClient()

    # Fetch the specific instrument, including user_id and market_and_symbol for logging
    stmt = select(
        Instrument.id,
        Instrument.yahoo_symbol,
        Instrument.user_id,
        Instrument.market_and_symbol,
    ).where(
        Instrument.id == instrument_id,
        Instrument.yahoo_symbol.isnot(None),
        Instrument.yahoo_symbol != "",
    )
    result = await session.execute(stmt)
    instrument = result.first()

    if not instrument:
        logger.warning(f"Instrument {instrument_id} not found or has no Yahoo symbol")
        return False

    # Fetch dividend date
    instrument_id_uuid, dividend_datetime = await fetch_dividend_date_for_symbol(
        yahoo_client, instrument.yahoo_symbol, instrument.id
    )

    # Update the database
    if dividend_datetime:
        updated_count = await bulk_update_dividend_dates(
            session, [(instrument_id_uuid, dividend_datetime)]
        )

        # Log the action for the user
        if updated_count > 0:
            await log_message(
                message=f"Dividend date updated for instrument",
                description=f"Dividend date for instrument {instrument.market_and_symbol} was updated to {dividend_datetime.strftime('%Y-%m-%d')} from Yahoo Finance.",
                log_type="unspecified",
                user_id=instrument.user_id,
                extra={
                    "action": "single_dividend_date_update",
                    "instrument": instrument.market_and_symbol,
                    "yahoo_symbol": instrument.yahoo_symbol,
                    "dividend_date": dividend_datetime.isoformat(),
                },
            )
            logger.info(
                f"Logged dividend date update for user {instrument.user_id}, instrument {instrument_id}"
            )

        logger.info(
            f"Successfully updated dividend date for instrument {instrument_id}: {dividend_datetime}"
        )
        return updated_count > 0
    else:
        logger.info(f"No dividend date found for instrument {instrument_id}")
        return False
