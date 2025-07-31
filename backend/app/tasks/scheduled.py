import logging
import uuid

import dramatiq
from periodiq import cron

from app.db.deps import get_db_context
from app.services.fetch_dividend_dates import (
    fetch_and_update_all_dividend_dates,
    fetch_and_update_single_dividend_date,
)

logger = logging.getLogger(__name__)

MIDNIGHT_ON_SUNDAYS = cron("0 0 * * 0")


@dramatiq.actor(periodic=MIDNIGHT_ON_SUNDAYS)
async def poll_scheduled_tasks():
    """
    Main scheduled task that runs at midnight on Sundays.
    Currently executes the dividend date update task.
    """
    logger.info("Starting scheduled tasks execution")
    try:
        await update_dividend_dates()
        logger.info("Completed scheduled tasks execution")
    except Exception as e:
        logger.error(f"Error in scheduled tasks execution: {str(e)}")
        raise


@dramatiq.actor
async def update_dividend_dates():
    """
    Fetch and update dividend dates for all instruments with Yahoo symbols.
    Uses the shared service logic for data fetching and updating.
    """
    logger.info("Starting dividend dates update task")

    async with get_db_context() as session:
        try:
            updated_count = await fetch_and_update_all_dividend_dates(session)
            logger.info(
                f"Successfully completed dividend dates update task - {updated_count} instruments updated"
            )
        except Exception as e:
            logger.error(f"Error in update_dividend_dates: {str(e)}")
            raise


@dramatiq.actor
async def update_single_instrument_dividend(instrument_id: str):
    """
    Update dividend date for a single instrument. Useful for testing or manual updates.

    Args:
        instrument_id: UUID string of the instrument to update
    """
    logger.info(f"Starting dividend date update for instrument {instrument_id}")

    async with get_db_context() as session:
        try:
            # Convert string to UUID
            instrument_uuid = uuid.UUID(instrument_id)

            success = await fetch_and_update_single_dividend_date(
                session, instrument_uuid
            )

            if success:
                logger.info(
                    f"Successfully updated dividend date for instrument {instrument_id}"
                )
            else:
                logger.info(
                    f"No dividend date found or updated for instrument {instrument_id}"
                )

        except Exception as e:
            logger.error(
                f"Error updating dividend date for instrument {instrument_id}: {str(e)}"
            )
            raise
