import uuid
from datetime import datetime, timezone, timedelta

from app.services.logging.helper import log_message

from app.clients.ig.client import IGClient
from app.clients.ig.types import (
    ConfirmDealRequest,
    DealConfirmation,
    GetPositionByDealIdRequest,
    DeleteWorkingOrderRequest,
    WorkingOrdersResponse,
)
from app.db.deps import get_db_context
from app.db.crud import get_order_by_id, update_order, delete_order, get_user_by_id
from app.db.models import Order


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
            ig_client = await IGClient.create_for_user(user)

            confirm_request = ConfirmDealRequest(deal_reference=order.deal_reference)
            confirmation = await ig_client.confirm_deal(confirm_request)

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
        # IGClient lifecycle is managed by cache; do not close here.
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


async def check_order_conversion(order: Order) -> None:
    """
    Check if an order with a deal ID has been converted to a position.
    If converted, delete the order as it's no longer needed.

    Args:
        order: The order instance with deal_id to check
    """
    ig_client = None

    try:
        user = order.user

        # Create IG client for the user
        ig_client = await IGClient.create_for_user(user)

        # Check if position exists with the deal ID
        position_exists = False
        try:
            request = GetPositionByDealIdRequest(deal_id=order.deal_id)
            position = await ig_client.get_position_by_deal_id(request)
            position_exists = position is not None
        except Exception:
            # If we can't get the position, assume it doesn't exist
            position_exists = False

        if position_exists:
            # Order has been converted to a position, delete the order
            async with get_db_context() as db:
                await delete_order(db, order.id)

            await log_message(
                message=f"Order converted to position - Deal ID: {order.deal_id}",
                description=f"Order with deal ID {order.deal_id} has been successfully converted to a position. The order has been removed from tracking.",
                log_type="order",
                user_id=user.id,
                extra={
                    "deal_id": order.deal_id,
                    "order_id": str(order.id),
                    "action": "order_converted",
                    "instrument_epic": (
                        order.instrument.ig_epic if order.instrument else None
                    ),
                },
            )

    except Exception as e:
        # Log any unexpected errors
        await log_message(
            message=f"Error checking order conversion - Deal ID: {order.deal_id if order.deal_id else 'unknown'}",
            description=f"Unexpected error while checking order conversion: {str(e)}",
            log_type="error",
            user_id=user.id if "user" in locals() and user else None,
            extra={
                "deal_id": order.deal_id if order.deal_id else None,
                "order_id": str(order.id) if order.id else None,
                "action": "check_conversion_error",
                "error": str(e),
            },
        )

    finally:
        # IGClient lifecycle is managed by cache; do not close here.
        pass


async def delete_expired_orders_for_user(user_id: uuid.UUID) -> None:
    """
    Delete expired working orders for a user.

    This function fetches all working orders from IG for the user,
    checks their created_date_utc against the user's maximum_order_age_in_minutes setting,
    and deletes any orders that have exceeded the time limit.

    Args:
        user: The User object containing the user's settings and credentials
    """
    ig_client = None

    async with get_db_context() as db:
        user = await get_user_by_id(db, user_id)

        try:
            # Create IG client for the user
            ig_client = await IGClient.create_for_user(user)

            # Get user's maximum order age setting
            max_age_minutes = user.settings.maximum_order_age_in_minutes
            max_age = timedelta(minutes=max_age_minutes)
            current_time = datetime.now(timezone.utc)

            # Fetch all working orders from IG
            try:
                working_orders_response: WorkingOrdersResponse = (
                    await ig_client.get_working_orders()
                )
            except Exception as e:
                await log_message(
                    message="Failed to fetch working orders from IG",
                    description=f"Could not retrieve working orders for user: {str(e)}",
                    log_type="error",
                    user_id=user.id,
                    extra={
                        "action": "fetch_working_orders_failed",
                        "error": str(e),
                    },
                )
                return

            # Process each working order
            deleted_count = 0
            failed_deletions = 0

            for working_order_data in working_orders_response.working_orders:
                working_order = working_order_data.working_order_data

                if (
                    not working_order
                    or not working_order.deal_id
                    or not working_order.created_date_utc
                ):
                    continue

                try:
                    # Parse the created date (format: "2024-01-15T10:30:00")
                    created_date = working_order.created_date_utc.replace(
                        tzinfo=timezone.utc
                    )

                    # Check if order has exceeded maximum age
                    order_age = current_time - created_date

                    if order_age > max_age:
                        # Order is expired, delete it
                        try:
                            delete_request = DeleteWorkingOrderRequest(
                                deal_id=working_order.deal_id
                            )
                            await ig_client.delete_working_order(delete_request)
                            deleted_count += 1

                            await log_message(
                                message=f"Expired working order deleted - Deal ID: {working_order.deal_id}",
                                description=f"Working order with deal ID {working_order.deal_id} exceeded maximum age of {max_age_minutes} minutes and was deleted from IG.",
                                log_type="order",
                                user_id=user.id,
                                extra={
                                    "deal_id": working_order.deal_id,
                                    "action": "expired_working_order_deleted",
                                    "max_age_minutes": max_age_minutes,
                                    "actual_age_minutes": int(
                                        order_age.total_seconds() / 60
                                    ),
                                    "epic": working_order.epic,
                                    "order_size": (
                                        float(working_order.order_size)
                                        if working_order.order_size
                                        else None
                                    ),
                                    "direction": working_order.direction,
                                    "created_date_utc": str(
                                        working_order.created_date_utc
                                    ),
                                },
                            )

                        except Exception as e:
                            failed_deletions += 1
                            await log_message(
                                message=f"Failed to delete expired working order - Deal ID: {working_order.deal_id}",
                                description=f"Could not delete expired working order from IG: {str(e)}",
                                log_type="error",
                                user_id=user.id,
                                extra={
                                    "deal_id": working_order.deal_id,
                                    "action": "working_order_deletion_failed",
                                    "error": str(e),
                                    "epic": working_order.epic,
                                    "created_date_utc": str(
                                        working_order.created_date_utc
                                    ),
                                },
                            )

                except Exception as e:
                    # Error parsing date or calculating age
                    await log_message(
                        message=f"Error processing working order - Deal ID: {working_order.deal_id if working_order.deal_id else 'unknown'}",
                        description=f"Could not process working order for expiration check: {str(e)}",
                        log_type="error",
                        user_id=user.id,
                        extra={
                            "deal_id": (
                                working_order.deal_id if working_order.deal_id else None
                            ),
                            "action": "working_order_processing_error",
                            "error": str(e),
                            "created_date_utc": str(working_order.created_date_utc),
                        },
                    )

            # Log summary if any orders were processed
            total_orders = len(working_orders_response.working_orders)
            if total_orders > 0:
                await log_message(
                    message=f"Expired orders cleanup completed - {deleted_count} deleted, {failed_deletions} failed",
                    description=f"Processed {total_orders} working orders. Successfully deleted {deleted_count} expired orders, failed to delete {failed_deletions} orders.",
                    log_type="order",
                    user_id=user.id,
                    extra={
                        "action": "expired_orders_cleanup_summary",
                        "total_orders": total_orders,
                        "deleted_count": deleted_count,
                        "failed_deletions": failed_deletions,
                        "max_age_minutes": max_age_minutes,
                    },
                )

        except Exception as e:
            # Log any unexpected errors
            await log_message(
                message="Unexpected error during expired orders cleanup",
                description=f"Unexpected error while cleaning up expired orders for user: {str(e)}",
                log_type="error",
                user_id=user.id,
                extra={
                    "action": "expired_orders_cleanup_error",
                    "error": str(e),
                },
            )

        finally:
            # IGClient lifecycle is managed by cache; do not close here.
            pass
