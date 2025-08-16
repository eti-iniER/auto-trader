import logging

import dramatiq
from app.config import settings
from app.db.deps import get_db_context
from app.db.models import Order, Instrument, User
from app.services.dividend_dates import fetch_and_update_all_dividend_dates
from app.services.order_fulfillment import confirm_multiple_orders_deal_references
from dramatiq.brokers.rabbitmq import RabbitmqBroker
from dramatiq.middleware import AsyncIO
from periodiq import PeriodiqMiddleware, cron
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload, join

broker = RabbitmqBroker(url=settings.DRAMATIQ_BROKER_URL)
broker.add_middleware(AsyncIO())
broker.add_middleware(PeriodiqMiddleware(skip_delay=30))

dramatiq.set_broker(broker)

logger = logging.getLogger(__name__)

DIVIDEND_DATE_UPDATE_SCHEDULE = cron(settings.DIVIDEND_DATE_UPDATE_SCHEDULE)
ORDER_CONFIRMATION_SCHEDULE = cron("* * * * *")  # Every minute


@dramatiq.actor(periodic=ORDER_CONFIRMATION_SCHEDULE)
async def confirm_deal_references():
    """
    Confirm deal references for all orders in the database.
    Runs every minute using the order fulfillment service.
    """
    logger.info("Starting deal reference confirmation task")

    async with get_db_context() as db:
        try:
            # Fetch all orders with their associated instruments and users
            stmt = (
                select(Order).join_from(Order, Instrument).join_from(Instrument, User)
            )
            result = await db.execute(stmt)
            orders = result.scalars().all()

            if not orders:
                logger.info("No orders found to confirm")
                return

            # Use the service function to handle confirmation with caching
            confirmed_count, error_count = (
                await confirm_multiple_orders_deal_references(orders)
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
