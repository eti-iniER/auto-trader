import logging
from datetime import datetime, timezone, timedelta
from typing import List

import dramatiq
from app.config import settings
from app.db.deps import get_db_context
from app.db.models import Instrument, Order, User
from app.services.dividend_dates import fetch_and_update_all_dividend_dates
from app.services.order_fulfillment import confirm_multiple_orders_deal_references
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.middleware import AsyncIO
from periodiq import PeriodiqMiddleware, cron
from sqlalchemy.future import select
from sqlalchemy import delete

broker = RabbitmqBroker(url=settings.DRAMATIQ_BROKER_URL)
broker.add_middleware(AsyncIO())
broker.add_middleware(PeriodiqMiddleware(skip_delay=30))

dramatiq.set_broker(broker)

logger = logging.getLogger(__name__)

DIVIDEND_DATE_UPDATE_SCHEDULE = cron(settings.DIVIDEND_DATE_UPDATE_SCHEDULE)
ORDER_CONFIRMATION_SCHEDULE = cron("* * * * *")  # Every minute
ORDER_CLEANUP_SCHEDULE = cron(settings.ORDER_CLEANUP_SCHEDULE)


@dramatiq.actor(periodic=ORDER_CONFIRMATION_SCHEDULE)
async def confirm_deal_references():
    """
    Confirm deal references for all orders in the database.
    Runs every minute using the order fulfillment service.
    """
    logger.info("Starting deal reference confirmation task")

    async with get_db_context() as db:
        try:
            stmt = (
                select(Order).join_from(Order, Instrument).join_from(Instrument, User)
            )
            result = await db.execute(stmt)
            orders: List[Order] = result.scalars().all()

            if not orders:
                logger.info("No orders found to confirm")
                return

            # Use the service function to handle confirmation with caching
            confirmed_count, error_count = (
                await confirm_multiple_orders_deal_references(
                    [order.id for order in orders]
                )
            )

            logger.info(
                f"Deal reference confirmation task completed - "
                f"{confirmed_count} confirmed, {error_count} errors"
            )

        except Exception as e:
            logger.error(f"Error in confirm_deal_references task: {str(e)}")
            raise


@dramatiq.actor(periodic=DIVIDEND_DATE_UPDATE_SCHEDULE)
async def update_dividend_dates():
    """
    Fetch and update dividend dates for all instruments with Yahoo symbols.
    Uses the shared service logic for data fetching and updating.
    """
    logger.info("Starting dividend dates update task")

    async with get_db_context() as db:
        try:
            updated_count = await fetch_and_update_all_dividend_dates(db)
            logger.info(
                f"Successfully completed dividend dates update task - {updated_count} instruments updated"
            )
        except Exception as e:
            logger.error(f"Error in update_dividend_dates: {str(e)}")
            raise


@dramatiq.actor(periodic=ORDER_CLEANUP_SCHEDULE)
async def cleanup_old_orders():
    """
    Delete orders that are older than the configured number of hours.
    Runs on a configurable schedule (default: every 1 hours).
    """
    logger.info("Starting old orders cleanup task")

    async with get_db_context() as db:
        try:
            # Calculate the cutoff time
            cutoff_time = datetime.now(timezone.utc) - timedelta(
                hours=settings.ORDER_CLEANUP_HOURS
            )

            # Create delete statement for orders older than cutoff time
            stmt = delete(Order).where(Order.created_at < cutoff_time)

            # Execute the deletion
            result = await db.execute(stmt)
            deleted_count = result.rowcount

            # Commit the changes
            await db.commit()

            logger.info(
                f"Successfully completed old orders cleanup task - "
                f"{deleted_count} orders older than {settings.ORDER_CLEANUP_HOURS} hours deleted"
            )

        except Exception as e:
            logger.error(f"Error in cleanup_old_orders task: {str(e)}")
            await db.rollback()
            raise
