import uuid

from app.clients.ig.client import IGClient
from app.clients.ig.types import (
    ConfirmDealRequest,
    DealConfirmation,
)
from app.db.deps import get_db_context
from app.db.crud import get_order_by_id, update_order


class OrderNotFoundError(Exception):
    pass


async def confirm_deal_reference_for_order(
    order_id: uuid.UUID,
) -> DealConfirmation | None:
    """
    Confirm deal reference for a single order.

    Returns:
        DealConfirmation: If the order confirmation is successful
        None: If the order is not found, confirmation fails, or any error occurs
    """
    ig_client = None

    try:
        async with get_db_context() as db:
            order = await get_order_by_id(db, order_id)
            if not order:
                raise OrderNotFoundError(f"Order {order_id} not found in database")

            user = order.instrument.user
            ig_client = IGClient.create_for_user(user)

            confirm_request = ConfirmDealRequest(deal_reference=order.deal_reference)
            confirmation = ig_client.confirm_deal(confirm_request)

            # Return None if confirmation fails
            if confirmation is None:
                return None

            # Update order with deal_id if we got one and don't have it yet
            if confirmation.deal_id and not order.deal_id:
                await update_order(db, order.id, {"deal_id": confirmation.deal_id})

            return confirmation

    except OrderNotFoundError:
        return None
    except Exception as e:
        from app.clients.ig.exceptions import IGAPIError, IGAuthenticationError

        # Handle IG API specific errors gracefully
        if isinstance(e, (IGAPIError, IGAuthenticationError)):
            return None

        # For other exceptions, return None to keep interface simple
        return None

    finally:
        if ig_client:
            try:
                ig_client.client.close()
            except Exception:
                pass
