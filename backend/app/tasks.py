import logging
import logging.config
from datetime import datetime, timedelta, timezone

import dramatiq
from app.api.schemas.webhook import WebhookPayload
from app.config import LOGGING_CONFIG, settings
from app.db.deps import get_db_context
from app.db.models import Order
from app.services.dividend_dates import fetch_and_update_all_dividend_dates
from app.services.order_fulfillment import check_order_conversion
from app.services.trading.handler import handle_alert
from app.db.crud import get_all_orders_with_deal_id
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.middleware import AsyncIO
from periodiq import PeriodiqMiddleware, cron
from sqlalchemy import delete

broker = RabbitmqBroker(url=settings.DRAMATIQ_BROKER_URL)
broker.add_middleware(AsyncIO())
broker.add_middleware(PeriodiqMiddleware(skip_delay=30))

dramatiq.set_broker(broker)

logging.config.dictConfig(LOGGING_CONFIG)

logger = logging.getLogger(__name__)

DIVIDEND_DATE_UPDATE_SCHEDULE = cron(settings.DIVIDEND_DATE_UPDATE_SCHEDULE)
ORDER_CLEANUP_SCHEDULE = cron(settings.ORDER_CLEANUP_SCHEDULE)
ORDER_CONVERSION_CHECK_SCHEDULE = cron(settings.ORDER_CONVERSION_CHECK_SCHEDULE)


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


@dramatiq.actor(periodic=ORDER_CONVERSION_CHECK_SCHEDULE, max_retries=3)
async def check_order_conversions():
    """
    Check all orders with deal IDs to see if they've been converted to positions.
    Runs every minute to monitor order status and clean up converted or expired orders.
    """
    logger.info("Starting order conversion check task")

    async with get_db_context() as db:
        try:
            # Get all orders that have deal IDs
            orders = await get_all_orders_with_deal_id(db)

            if not orders:
                logger.info("No orders with deal IDs found for conversion check")
                return

            logger.info(f"Checking conversion status for {len(orders)} orders")

            # Check each order for conversion
            for order in orders:
                try:
                    await check_order_conversion(order)
                except Exception as e:
                    logger.error(
                        f"Error checking conversion for order {order.id} "
                        f"(deal_id: {order.deal_id}): {str(e)}"
                    )
                    # Continue with other orders even if one fails

            logger.info("Successfully completed order conversion check task")

        except Exception as e:
            logger.error(f"Error in check_order_conversions task: {str(e)}")
            raise


@dramatiq.actor(max_retries=0)
async def handle_trading_alert(payload_dict: dict):
    """
    Actor that wraps the handle_alert function for processing TradingView webhook alerts.

    Args:
        payload_dict: Dictionary representation of the WebhookPayload
    """
    logger.info(f"Processing trading alert: {payload_dict}")

    try:
        # Convert the dictionary back to WebhookPayload
        payload = WebhookPayload.model_validate(payload_dict)

        # Call the handle_alert function
        await handle_alert(payload)

        logger.info("Successfully processed trading alert")

    except Exception as e:
        logger.error(f"Error processing trading alert: {str(e)}")
        raise
