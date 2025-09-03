import uuid

from app.services.logging.helper import log_message

from app.clients.ig.client import IGClient
from app.clients.ig.types import (
    ConfirmDealRequest,
    DealConfirmation,
)
from app.db.deps import get_db_context
from app.db.crud import get_order_by_id, update_order, delete_order


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


# Log the outcome of an order confirmation for a user
async def log_order_confirmation_outcome(confirmation, user):
    """
    Creates a log entry for the given user explaining the outcome of the order confirmation.
    Args:
        confirmation (DealConfirmation | None): The confirmation object or None.
        user (User): The user for whom to create the log.
    """
    if confirmation is None:
        message = "Order confirmation failed"
        description = "No confirmation was received for the order. This could indicate a network issue, API error, or the deal reference was invalid."
        extra = {"confirmation_status": "failed", "reason": "no_confirmation_received"}
        log_type = "order"
        await log_message(message, description, log_type, user_id=user.id, extra=extra)
        return

    # Success: build a message from confirmation details with explicit status
    if confirmation.deal_status == "ACCEPTED":
        message = f"Order accepted: Deal ID {confirmation.deal_id}"
    elif confirmation.deal_status == "REJECTED":
        message = f"Order rejected: Deal ID {confirmation.deal_id}"
    else:
        message = (
            f"Order {confirmation.deal_status.lower()}: Deal ID {confirmation.deal_id}"
        )

    description = f"Order confirmed for epic {confirmation.epic} with direction {confirmation.direction}. Deal status: {confirmation.deal_status}. Reason: {confirmation.reason}"

    # Add profit information if available
    if confirmation.profit is not None:
        profit_info = f"{confirmation.profit}"
        if confirmation.profit_currency:
            profit_info += f" {confirmation.profit_currency}"
        description += f". Profit: {profit_info}"

    extra = {
        "confirmation_status": "success",
        "deal_id": confirmation.deal_id,
        "deal_reference": confirmation.deal_reference,
        "deal_status": confirmation.deal_status,
        "epic": confirmation.epic,
        "direction": confirmation.direction,
        "reason": confirmation.reason,
        "size": float(confirmation.size) if confirmation.size else None,
        "level": float(confirmation.level) if confirmation.level else None,
        "profit": float(confirmation.profit) if confirmation.profit else None,
        "profit_currency": confirmation.profit_currency,
    }

    log_type = "order"
    await log_message(message, description, log_type, user_id=user.id, extra=extra)


async def delete_rejected_order(
    confirmation: DealConfirmation, order_id: uuid.UUID
) -> bool:
    """
    Deletes an order from the database if the confirmation indicates it was rejected.

    Args:
        confirmation (DealConfirmation): The confirmation object from IG API
        order_id (uuid.UUID): The ID of the order to potentially delete

    Returns:
        bool: True if the order was deleted, False if it wasn't rejected or deletion failed
    """
    if confirmation is None or confirmation.deal_status != "REJECTED":
        return False

    try:
        async with get_db_context() as db:
            await delete_order(db, order_id)
            return True
    except Exception:
        # If deletion fails, return False but don't raise
        # The calling code can decide how to handle this
        return False
