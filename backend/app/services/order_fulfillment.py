import datetime
import logging
from typing import Dict, List, Optional, Tuple

from app.clients.ig.client import IGClient
from app.clients.ig.types import (
    ConfirmDealRequest,
    DealConfirmation,
    DeleteWorkingOrderRequest,
)
from app.db.deps import get_db_context
from app.db.crud import delete_order, get_order_by_id
from app.db.models import Order
from app.services.logging import log_message
import uuid

logger = logging.getLogger(__name__)


async def confirm_multiple_orders_deal_references(
    order_ids: List[uuid.UUID],
) -> Tuple[int, int]:
    """
    Confirm deal references for multiple orders using cached IG clients.

    Args:
        orders: List of orders to confirm deal references for

    Returns:
        Tuple of (confirmed_count, error_count)
    """
    if not order_ids:
        logger.info("No orders provided to confirm")
        return 0, 0

    # Cache IG clients by user to avoid creating multiple clients for the same user
    ig_clients_cache: Dict[str, IGClient] = {}
    confirmed_count = 0
    error_count = 0

    try:
        async with get_db_context() as db:
            orders = [await get_order_by_id(db, order_id) for order_id in order_ids]

            for order in orders:
                try:
                    user = order.instrument.user
                    user_id_str = str(user.id)

                    if user_id_str not in ig_clients_cache:
                        ig_clients_cache[user_id_str] = IGClient.create_for_user(user)

                    ig_client = ig_clients_cache[user_id_str]

                    confirmation = await confirm_order_deal_reference(order, ig_client)

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
                        await delete_order(order.id)
                        await ig_client.delete_working_order(
                            DeleteWorkingOrderRequest(deal_id=confirmation.deal_id)
                        )
                        continue

                    confirmed_count += 1

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

                except Exception as e:
                    logger.error(
                        f"Error confirming deal reference for order {order.id}: {str(e)}"
                    )
                    error_count += 1

    finally:
        for ig_client in ig_clients_cache.values():
            try:
                ig_client.client.close()
            except Exception as e:
                logger.warning(f"Error closing IG client: {str(e)}")

    return confirmed_count, error_count


async def confirm_order_deal_reference(
    order: Order, ig_client: Optional[IGClient] = None
) -> Optional[DealConfirmation]:
    """
    Confirm the deal reference for a given order using the IG API.

    Args:
        order: The order to confirm the deal reference for
        ig_client: Optional IG client to use. If not provided, will create one for the order's user

    Returns:
        DealConfirmation if successful, None if failed

    Raises:
        Exception: If there's an error during the confirmation process
    """
    try:
        # Create IG client if not provided
        client_provided = ig_client is not None
        if not client_provided:
            ig_client = IGClient.create_for_user(order.instrument.user)

        # Create the confirm deal request
        confirm_request = ConfirmDealRequest(deal_reference=order.deal_reference)

        # Call the confirmation method
        confirmation = ig_client.get_working_order_confirmation(confirm_request)

        logger.info(
            f"Successfully confirmed deal reference {order.deal_reference} "
            f"for user {order.instrument.user.email} - Status: {confirmation.deal_status}"
        )

        return confirmation

    except Exception as e:
        logger.error(f"Error confirming deal reference for order {order.id}: {str(e)}")
        raise

    finally:
        # Only close the client if we created it ourselves
        if not client_provided and ig_client:
            try:
                ig_client.client.close()
            except Exception as e:
                logger.warning(f"Error closing IG client: {str(e)}")
