import datetime
import logging
import uuid

from app.clients.ig.client import IGClient
from app.clients.ig.types import (
    ConfirmDealRequest,
    DeleteWorkingOrderRequest,
)
from app.db.deps import get_db_context
from app.db.crud import delete_order, get_order_by_id
from app.services.logging import log_message

logger = logging.getLogger(__name__)


async def confirm_single_order_deal_reference(
    order_id: uuid.UUID,
) -> bool:
    """
    Confirm deal reference for a single order.

    Args:
        order_id: UUID of the order to confirm deal reference for

    Returns:
        bool: True if successful, False if failed
    """
    try:
        async with get_db_context() as db:
            order = await get_order_by_id(db, order_id)
            if not order:
                logger.error(f"Order {order_id} not found")
                return False

            user = order.instrument.user
            ig_client = IGClient.create_for_user(user)

            try:
                # Create the confirm deal request and get confirmation
                confirm_request = ConfirmDealRequest(
                    deal_reference=order.deal_reference
                )
                confirmation = ig_client.get_working_order_confirmation(confirm_request)

                logger.info(
                    f"Successfully confirmed deal reference {order.deal_reference} "
                    f"for user {user.email} - Status: {confirmation.deal_status}"
                )

                # Check if order age exceeds the maximum allowed age
                now = datetime.datetime.now(datetime.timezone.utc)
                order_age = now - order.created_at
                max_age = datetime.timedelta(
                    minutes=user.settings.maximum_order_age_in_minutes
                )

                if order_age > max_age:
                    await log_message(
                        f"Order {order.id} exceeded maximum age ({order_age} > {max_age}), deleting",
                        description=f"Order created at {order.created_at}, current time {now}",
                        user_id=user.id,
                        extra={
                            "order_in_db_id": str(order.id),
                            "order_age": str(order_age),
                            "max_age": str(max_age),
                            "order_created_at": order.created_at.isoformat(),
                            "current_time": now.isoformat(),
                        },
                    )
                    await delete_order(db, order.id)
                    await ig_client.delete_working_order(
                        DeleteWorkingOrderRequest(deal_id=confirmation.deal_id)
                    )
                    return True

                if confirmation.deal_status == "REJECTED":
                    await log_message(
                        f"Order for instrument with IG Epic {order.instrument.ig_epic} was rejected: {confirmation.reason}",
                        description=confirmation.reason,
                        user_id=user.id,
                        extra={
                            "confirmation_payload": confirmation.model_dump(
                                mode="json"
                            ),
                            "order_in_db_id": str(order.id),
                            "deal_reference": confirmation.deal_reference,
                            "deal_id": confirmation.deal_id,
                            "deal_status": confirmation.deal_status,
                        },
                    )
                    await delete_order(db, order.id)
                    return True

                logger.info(
                    f"Successfully confirmed deal reference for order {order_id}"
                )
                return True

            finally:
                try:
                    ig_client.client.close()
                except Exception as e:
                    logger.warning(f"Error closing IG client: {str(e)}")

    except Exception as e:
        logger.error(f"Error confirming deal reference for order {order_id}: {str(e)}")
        return False
