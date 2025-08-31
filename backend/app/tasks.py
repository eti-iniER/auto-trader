import logging
from datetime import datetime, timedelta, timezone

import dramatiq
from app.config import settings
from app.db.deps import get_db_context
from app.db.models import Order
from app.services.dividend_dates import fetch_and_update_all_dividend_dates
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.middleware import AsyncIO
from periodiq import PeriodiqMiddleware, cron
from sqlalchemy import delete

broker = RabbitmqBroker(url=settings.DRAMATIQ_BROKER_URL)
broker.add_middleware(AsyncIO())
broker.add_middleware(PeriodiqMiddleware(skip_delay=30))

dramatiq.set_broker(broker)

logger = logging.getLogger(__name__)

DIVIDEND_DATE_UPDATE_SCHEDULE = cron(settings.DIVIDEND_DATE_UPDATE_SCHEDULE)
ORDER_CLEANUP_SCHEDULE = cron(settings.ORDER_CLEANUP_SCHEDULE)


@dramatiq.actor(max_retries=0)
async def confirm_single_deal_reference(order_id: str):
    """
    Confirm deal reference for a single order.
    This task is triggered immediately after an order is created.

    Args:
        order_id: The UUID string of the order to confirm
    """
    logger.info(f"Starting deal reference confirmation for order {order_id}")

    try:
        # Convert string back to UUID
        import uuid
        from app.services.order_fulfillment import (
            confirm_single_order_deal_reference_with_retry,
        )

        order_uuid = uuid.UUID(order_id)

        # Use the enhanced confirmation function with retry logic and user logging
        await confirm_single_order_deal_reference_with_retry(order_uuid)
        logger.info(
            f"Successfully completed deal reference confirmation for order {order_id}"
        )

    except Exception as e:
        logger.error(
            f"Error in confirm_single_deal_reference task for order {order_id}: {str(e)}"
        )
        raise


@dramatiq.actor(periodic=DIVIDEND_DATE_UPDATE_SCHEDULE, max_retries=3)
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


@dramatiq.actor(periodic=ORDER_CLEANUP_SCHEDULE, max_retries=3)
async def cleanup_old_orders():
    """
    Delete orders that are older than the configured number of hours.
    Runs on a configurable schedule (default: every 24 hours).
    """
    logger.info("Starting old orders cleanup task")

    async with get_db_context() as db:
        try:
            # Calculate the cutoff time
            cutoff_time = datetime.now(timezone.utc) - timedelta(
                hours=settings.ORDER_CLEANUP_HOURS
            )

            # Create delete statement for open orders older than cutoff time
            stmt = delete(Order).where(
                Order.created_at < cutoff_time, Order.is_open == True
            )

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
