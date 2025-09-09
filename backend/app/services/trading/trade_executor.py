from decimal import Decimal
from typing import Literal, Union

from app.clients.ig import IGClient
from app.clients.ig.types import (
    CreatePositionRequest,
    CreateWorkingOrderRequest,
)
from app.config import settings
from app.db.crud import create_order_for_instrument
from app.db.deps import get_db_context
from app.db.models import Instrument, Order, User
from app.services.logging import log_message
from app.services.order_fulfillment import (
    confirm_deal_reference_for_order,
    log_order_confirmation_outcome,
    delete_rejected_order,
)


def _create_request_object(
    user: User,
    instrument: Instrument,
    direction: Literal["BUY", "SELL"],
    limit_distance: Decimal,
    limit_price: Decimal,
    stop_loss_distance: Decimal,
    size: Decimal,
) -> Union[CreatePositionRequest, CreateWorkingOrderRequest]:
    """Create the appropriate request object based on user's order type setting."""
    if user.settings.order_type.value == "MARKET":
        return CreatePositionRequest(
            currency_code=settings.DEFAULT_CURRENCY_CODE,
            direction=direction,
            epic=instrument.ig_epic,
            expiry="DEC-27",  # Expiry date gotten from making orders via IG's dashboard when set to "Good till cancelled"
            force_open=True,
            guaranteed_stop=False,
            level=None,  # No level for market orders
            limit_distance=limit_distance,
            order_type="MARKET",
            size=size,
            stop_distance=stop_loss_distance,
        )
    else:
        return CreateWorkingOrderRequest(
            currency_code=settings.DEFAULT_CURRENCY_CODE,
            direction=direction,
            stop_distance=stop_loss_distance,
            limit_distance=limit_distance,
            epic=instrument.ig_epic,
            expiry="DEC-27",  # Expiry date gotten from making orders via IG's dashboard when set to "Good till cancelled"
            force_open=False,
            size=size,
            good_till_date=None,
            guaranteed_stop=False,
            level=limit_price,
            type="LIMIT",
            time_in_force="GOOD_TILL_CANCELLED",
        )


async def _execute_ig_request(
    ig_client: IGClient,
    request: Union[CreatePositionRequest, CreateWorkingOrderRequest],
) -> None:
    """Execute the appropriate IG API call based on request type."""
    if isinstance(request, CreatePositionRequest):
        await ig_client.create_position(request)
    else:
        await ig_client.create_working_order(request)


async def _log_order_success(
    user: User,
    instrument: Instrument,
    request: Union[CreatePositionRequest, CreateWorkingOrderRequest],
    order_in_db: Order,
) -> None:
    """Log successful order creation with appropriate messages."""
    is_market_order = isinstance(request, CreatePositionRequest)

    title = "Market position created" if is_market_order else "Order request created"
    message_prefix = "A market position" if is_market_order else "An order request"
    identifier = (
        "market_position_created" if is_market_order else "order_request_created"
    )

    await log_message(
        title,
        f"{message_prefix} for instrument with IG Epic {instrument.ig_epic} was {'created' if is_market_order else 'made'} successfully. Order type: {user.settings.order_type.value}. Deal reference: {order_in_db.deal_reference}",
        "order",
        user_id=user.id,
        identifier=identifier,
        extra={
            (
                "order_request" if not is_market_order else "position_request"
            ): request.model_dump(mode="json"),
            "instrument_ig_epic": instrument.ig_epic,
            "order_type": user.settings.order_type.value,
            "deal_reference": order_in_db.deal_reference,
            "order_id": str(order_in_db.id),
        },
    )


async def _cleanup_failed_order(user: User, order_id: str, error: Exception) -> None:
    """Clean up database order when IG API call fails."""
    try:
        from app.db.crud import delete_order

        async with get_db_context() as db:
            await delete_order(db, order_id)
    except Exception as cleanup_e:
        await log_message(
            "Failed to clean up order after IG error",
            f"Could not delete order {order_id} after IG order creation failed: {str(cleanup_e)}",
            "order",
            user_id=user.id,
            extra={
                "order_id": order_id,
                "cleanup_error": str(cleanup_e),
                "original_error": str(error),
            },
        )


async def _log_order_failure(
    user: User,
    instrument: Instrument,
    request: Union[CreatePositionRequest, CreateWorkingOrderRequest],
    error: Exception,
) -> None:
    """Log order creation failure with appropriate messages."""
    is_market_order = isinstance(request, CreatePositionRequest)

    title = (
        "Failed to create market position"
        if is_market_order
        else "Failed to create order"
    )
    error_prefix = "market position" if is_market_order else "working order"

    await log_message(
        title,
        f"Error creating {error_prefix} for instrument {instrument.ig_epic}: {str(error)}",
        "order",
        user_id=user.id,
        extra={
            (
                "order_request" if not is_market_order else "position_request"
            ): request.model_dump(mode="json"),
            "user_email": user.email,
            "instrument_ig_epic": instrument.ig_epic,
            "order_type": user.settings.order_type.value,
        },
    )


async def create_order(
    user: User,
    instrument: Instrument,
    direction: Literal["BUY", "SELL"],
    limit_distance: Decimal,
    limit_price: Decimal,
    stop_loss_distance: Decimal,
    size: Decimal,
) -> Order:
    ig_client = await IGClient.create_for_user(user)

    # Create the appropriate request object based on order type
    request = _create_request_object(
        user,
        instrument,
        direction,
        limit_distance,
        limit_price,
        stop_loss_distance,
        size,
    )

    try:
        # Create database order first to get deal_reference
        async with get_db_context() as db:
            order_in_db = await create_order_for_instrument(db, instrument)
            request.deal_reference = order_in_db.deal_reference

        # Execute the IG API call
        await _execute_ig_request(ig_client, request)

        # Log success
        await _log_order_success(user, instrument, request, order_in_db)

        # Handle confirmation and cleanup
        confirmation = await confirm_deal_reference_for_order(order_in_db.id)
        await log_order_confirmation_outcome(confirmation, user)
        await delete_rejected_order(confirmation, order_in_db.id)

        return order_in_db

    except Exception as e:
        # Clean up the database order if it was created but IG call failed
        if "order_in_db" in locals():
            await _cleanup_failed_order(user, order_in_db.id, e)

        # Log the failure
        await _log_order_failure(user, instrument, request, e)
        raise
