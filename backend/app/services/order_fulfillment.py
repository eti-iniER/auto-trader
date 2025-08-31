import datetime
import logging
import uuid

import tenacity
from app.clients.ig.client import IGClient
from app.clients.ig.types import (
    ConfirmDealRequest,
    DeleteWorkingOrderRequest,
    DealConfirmation,
)
from app.db.deps import get_db_context
from app.db.crud import delete_order, get_order_by_id
from app.services.logging import log_message

logger = logging.getLogger(__name__)


class OrderConfirmationError(Exception):
    """Custom exception for order confirmation failures that should trigger retries"""

    pass


class OrderNotFoundError(Exception):
    """Exception for when order is not found - should not trigger retries"""

    pass


async def confirm_single_order_deal_reference_with_retry(
    order_id: uuid.UUID,
) -> None:
    """
    Confirm deal reference for a single order with retry logic and comprehensive user logging.

    Args:
        order_id: UUID of the order to confirm deal reference for

    Raises:
        Exception: If confirmation fails after all retries
    """

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=1, max=5),
        retry=tenacity.retry_if_exception_type(OrderConfirmationError),
        reraise=True,
    )
    async def confirm_with_retry():
        """Inner function that handles the actual confirmation with retries"""
        confirmation = await confirm_single_order_deal_reference(order_id)

        # If confirmation is None due to API error or temporary issue, retry
        if confirmation is None:
            raise OrderConfirmationError(
                "Confirmation returned None - possible API error"
            )

        return confirmation

    user_id = None

    try:
        # Get user_id early for logging purposes
        async with get_db_context() as db:
            order = await get_order_by_id(db, order_id)

            if order:
                user_id = order.instrument.user.id

        confirmation = await confirm_with_retry()

        # Log successful confirmation
        await _log_confirmation_result(order_id, confirmation, user_id)

    except OrderNotFoundError:
        # Don't retry for non-existent orders
        logger.error(f"Order {order_id} not found - skipping confirmation")
        if user_id:
            await log_message(
                message="Order not found during confirmation",
                description=f"Order {order_id} was not found in database",
                user_id=user_id,
                log_type="order",
                extra={"order_id": str(order_id), "error": "order_not_found"},
            )

    except tenacity.RetryError as e:
        # All retries failed - delete order and log failure
        await _handle_confirmation_failure(order_id, user_id, e)
        raise

    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error during order confirmation {order_id}: {str(e)}")
        if user_id:
            await log_message(
                message="Unexpected error during order confirmation",
                description=f"Order {order_id} confirmation failed with unexpected error: {str(e)}",
                user_id=user_id,
                log_type="order",
                extra={"order_id": str(order_id), "error": str(e)},
            )
        raise


async def _log_confirmation_result(
    order_id: uuid.UUID, confirmation: DealConfirmation, user_id: uuid.UUID
):
    """Log the confirmation result based on deal status"""

    base_extra = {
        "order_id": str(order_id),
        "deal_status": confirmation.deal_status,
        "deal_reference": confirmation.deal_reference,
        "deal_id": confirmation.deal_id,
        "confirmation_payload": confirmation.model_dump(mode="json"),
    }

    if confirmation.deal_status == "ACCEPTED":
        await log_message(
            message="Order confirmed and ACCEPTED",
            description=f"Order {order_id} was accepted by IG with deal reference: {confirmation.deal_reference}",
            user_id=user_id,
            log_type="order",
            extra=base_extra,
        )
    elif confirmation.deal_status == "REJECTED":
        await log_message(
            message="Order confirmed but REJECTED",
            description=f"Order {order_id} was rejected by IG - reason: {getattr(confirmation, 'reason', 'Unknown')}",
            user_id=user_id,
            log_type="order",
            extra={
                **base_extra,
                "rejection_reason": getattr(confirmation, "reason", "Unknown"),
            },
        )
    else:
        await log_message(
            message=f"Order confirmed with status: {confirmation.deal_status}",
            description=f"Order {order_id} was confirmed with unexpected status: {confirmation.deal_status}",
            user_id=user_id,
            log_type="order",
            extra=base_extra,
        )


async def _handle_confirmation_failure(
    order_id: uuid.UUID, user_id: uuid.UUID, retry_error: tenacity.RetryError
):
    """Handle confirmation failure after all retries"""

    try:
        async with get_db_context() as db:
            if not user_id:
                # Try to get user_id if we don't have it
                order = await get_order_by_id(db, order_id)
                user_id = order.instrument.user.id

            # Log the failure
            error_message = str(retry_error.last_attempt.exception())

            if user_id:
                if "Confirmation returned None" in error_message:
                    # This is the expected case - order was rejected by IG
                    await log_message(
                        message="Order REJECTED by IG",
                        description=f"Order {order_id} was rejected by IG Markets (no confirmation received after 3 attempts)",
                        user_id=user_id,
                        log_type="order",
                        extra={
                            "order": order_id,
                            "deal_status": "REJECTED",
                            "retry_attempts": 3,
                            "confirmation_result": None,
                            "rejection_reason": "No confirmation received from IG",
                        },
                    )
                else:
                    # This would be an unexpected technical error
                    await log_message(
                        message="Order confirmation failed due to technical error",
                        description=f"Order {order_id} confirmation failed after all retries due to: {error_message}",
                        user_id=user_id,
                        log_type="order",
                        extra={
                            "order_id": str(order_id),
                            "retry_attempts": 3,
                            "final_error": error_message,
                            "retry_error_type": "tenacity.RetryError",
                        },
                    )

            # Delete the order
            await delete_order(db, order_id)

            if user_id:
                await log_message(
                    message="Order deleted after failed confirmation retries",
                    description=f"Order {order_id} deleted from database due to failed confirmation after retries.",
                    user_id=user_id,
                    log_type="order",
                    extra={
                        "order_id": str(order_id),
                        "retry_attempts": 3,
                        "action": "delete_order_after_failed_confirmation",
                    },
                )

    except Exception as delete_error:
        logger.error(
            f"Failed to delete order {order_id} after confirmation failure: {str(delete_error)}"
        )
        if user_id:
            await log_message(
                message="Failed to delete order after confirmation failure",
                description=f"Failed to delete order {order_id} after confirmation failure: {str(delete_error)}",
                user_id=user_id,
                log_type="order",
                extra={
                    "order_id": str(order_id),
                    "retry_attempts": 3,
                    "delete_error": str(delete_error),
                    "action": "delete_order_failed",
                },
            )


async def confirm_single_order_deal_reference(order_id: uuid.UUID):
    """
    Confirm deal reference for a single order.

    Args:
        order_id: UUID of the order to confirm deal reference for

    Returns:
        Confirmation object if successful, None if failed

    Raises:
        OrderNotFoundError: If order doesn't exist in database
    """
    ig_client = None

    try:
        async with get_db_context() as db:
            order = await get_order_by_id(db, order_id)
            if not order:
                logger.error(f"Order {order_id} not found")
                raise OrderNotFoundError(f"Order {order_id} not found in database")

            user = order.instrument.user
            ig_client = IGClient.create_for_user(user)

            # Create the confirm deal request and get confirmation
            confirm_request = ConfirmDealRequest(deal_reference=order.deal_reference)
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
                await _handle_expired_order(
                    order, confirmation, user, now, order_age, max_age, db, ig_client
                )
                return confirmation

            if confirmation.deal_status == "REJECTED":
                await _handle_rejected_order(order, confirmation, user, db)
                return confirmation

            logger.info(f"Successfully confirmed deal reference for order {order_id}")
            return confirmation

    except OrderNotFoundError:
        # Re-raise so it's not retried
        raise

    except Exception as e:
        logger.error(f"Error confirming deal reference for order {order_id}: {str(e)}")
        return None

    finally:
        if ig_client:
            try:
                ig_client.client.close()
            except Exception as e:
                logger.warning(f"Error closing IG client: {str(e)}")


async def _handle_expired_order(
    order, confirmation: DealConfirmation, user, now, order_age, max_age, db, ig_client
):
    """Handle orders that have exceeded maximum age"""
    await log_message(
        message=f"Order {order.id} exceeded maximum age ({order_age} > {max_age}), deleting",
        description=f"Order created at {order.created_at}, current time {now}",
        user_id=user.id,
        log_type="order",
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


async def _handle_rejected_order(order, confirmation: DealConfirmation, user, db):
    """Handle rejected orders"""
    await log_message(
        message=f"Order for instrument with IG Epic {order.instrument.ig_epic} was rejected: {confirmation.reason}",
        description=confirmation.reason,
        user_id=user.id,
        log_type="order",
        extra={
            "confirmation_payload": confirmation.model_dump(mode="json"),
            "order_in_db_id": str(order.id),
            "deal_reference": confirmation.deal_reference,
            "deal_id": confirmation.deal_id,
            "deal_status": confirmation.deal_status,
        },
    )
    await delete_order(db, order.id)
