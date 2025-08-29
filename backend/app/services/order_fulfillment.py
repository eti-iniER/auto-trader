import datetime
import logging
import uuid

import tenacity
from app.clients.ig.client import IGClient
from app.clients.ig.types import (
    ConfirmDealRequest,
    DeleteWorkingOrderRequest,
)
from app.db.deps import get_db_context
from app.db.crud import delete_order, get_order_by_id
from app.services.logging import log_message

logger = logging.getLogger(__name__)


async def confirm_single_order_deal_reference_with_retry(
    order_id: uuid.UUID,
) -> None:
    """
    Confirm deal reference for a single order with retry logic and comprehensive user logging.
    This function includes tenacity retry logic and detailed user-specific logging.

    Args:
        order_id: UUID of the order to confirm deal reference for

    Raises:
        Exception: If confirmation fails after all retries
    """

    @tenacity.retry(
        stop=tenacity.stop_after_attempt(3),
        wait=tenacity.wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def confirm_with_retry():
        confirmation = await confirm_single_order_deal_reference(order_id)

        if confirmation is None:
            # Log each failed attempt
            logger.warning(
                f"Confirmation attempt failed for order {order_id} - got None, retrying..."
            )
            raise Exception("Confirmation returned None, retrying...")

        return confirmation

    try:
        confirmation = await confirm_with_retry()

        # This block is now unreachable since confirm_with_retry will either succeed or raise RetryError
        # Removing the unreachable if confirmation is None check

        # Get order and user information for logging
        async with get_db_context() as db:
            order = await get_order_by_id(db, order_id)
            user_id = order.instrument.user.id

        # Check deal status and log appropriately using log_message
        if confirmation.deal_status == "ACCEPTED":
            await log_message(
                message=f"Order confirmed and ACCEPTED",
                description=f"Order {order_id} was accepted by IG with deal reference: {confirmation.deal_reference}",
                user_id=user_id,
                log_type="order",
                extra={
                    "order_id": str(order_id),
                    "deal_status": confirmation.deal_status,
                    "deal_reference": confirmation.deal_reference,
                    "deal_id": confirmation.deal_id,
                    "confirmation_payload": confirmation.model_dump(mode="json"),
                },
            )
        elif confirmation.deal_status == "REJECTED":
            await log_message(
                message=f"Order confirmed but REJECTED",
                description=f"Order {order_id} was rejected by IG - reason: {getattr(confirmation, 'reason', 'Unknown')}",
                user_id=user_id,
                log_type="order",
                extra={
                    "order_id": str(order_id),
                    "deal_status": confirmation.deal_status,
                    "deal_reference": confirmation.deal_reference,
                    "deal_id": confirmation.deal_id,
                    "rejection_reason": getattr(confirmation, "reason", "Unknown"),
                    "confirmation_payload": confirmation.model_dump(mode="json"),
                },
            )
        else:
            await log_message(
                message=f"Order confirmed with status: {confirmation.deal_status}",
                description=f"Order {order_id} was confirmed with unexpected status: {confirmation.deal_status}",
                user_id=user_id,
                log_type="order",
                extra={
                    "order_id": str(order_id),
                    "deal_status": confirmation.deal_status,
                    "deal_reference": confirmation.deal_reference,
                    "deal_id": confirmation.deal_id,
                    "confirmation_payload": confirmation.model_dump(mode="json"),
                },
            )

    except tenacity.RetryError as e:
        # Delete the order from database if all retries failed
        try:
            async with get_db_context() as db:
                # Get order to access user information for logging
                try:
                    order = await get_order_by_id(db, order_id)
                    user_id = order.instrument.user.id

                    # Check if the error was due to confirmation returning None
                    error_message = str(e.last_attempt.exception())
                    if "Confirmation returned None" in error_message:
                        await log_message(
                            message=f"Failed to confirm order after 3 attempts - confirmation returned None",
                            description=f"Order {order_id} confirmation returned None after all 3 retry attempts, deleting order",
                            user_id=user_id,
                            log_type="order",
                            extra={
                                "order_id": str(order_id),
                                "retry_attempts": 3,
                                "confirmation_result": None,
                                "failure_reason": "confirmation_returned_none",
                            },
                        )
                    else:
                        await log_message(
                            message=f"Failed to confirm order after 3 retry attempts",
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
                except Exception as log_error:
                    logger.warning(f"Could not log message for user: {str(log_error)}")

                await delete_order(db, order_id)
            logger.info(
                f"Deleted order {order_id} from database due to failed confirmation after retries"
            )
        except Exception as delete_error:
            logger.error(
                f"Failed to delete order {order_id} after confirmation failure: {str(delete_error)}"
            )
        raise


async def confirm_single_order_deal_reference(
    order_id: uuid.UUID,
):
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
                return None

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
                    return confirmation

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
                    return confirmation

                logger.info(
                    f"Successfully confirmed deal reference for order {order_id}"
                )
                return confirmation

            finally:
                try:
                    ig_client.client.close()
                except Exception as e:
                    logger.warning(f"Error closing IG client: {str(e)}")

    except Exception as e:
        logger.error(f"Error confirming deal reference for order {order_id}: {str(e)}")
        return None
