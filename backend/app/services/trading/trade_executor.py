from decimal import Decimal
from typing import Literal

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
from app.services.order_fulfillment import confirm_deal_reference_for_order


async def create_order(
    user: User,
    instrument: Instrument,
    direction: Literal["BUY", "SELL"],
    limit_distance: Decimal,
    limit_price: Decimal,
    stop_loss_distance: Decimal,
    size: Decimal,
) -> Order:
    ig_client = IGClient.create_for_user(user)

    if user.settings.order_type.value == "MARKET":
        # Use CreatePositionRequest for market orders
        position_request = CreatePositionRequest(
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

        try:
            # Create database order first to get deal_reference
            async with get_db_context() as db:
                order_in_db = await create_order_for_instrument(db, instrument)
                position_request.deal_reference = order_in_db.deal_reference

            # Now create the position with the deal_reference
            ig_client.create_position(position_request)

            await log_message(
                "Market position created",
                f"A market position for instrument with IG Epic {instrument.ig_epic} was created successfully. Order type: {user.settings.order_type.value}. Deal reference: {order_in_db.deal_reference}",
                "order",
                user_id=user.id,
                identifier="market_position_created",
                extra={
                    "position_request": position_request.model_dump(mode="json"),
                    "instrument_ig_epic": instrument.ig_epic,
                    "order_type": user.settings.order_type.value,
                    "deal_reference": order_in_db.deal_reference,
                    "order_id": str(order_in_db.id),
                },
            )

            await confirm_deal_reference_for_order(order_in_db.id)

            return order_in_db

        except Exception as e:
            # Clean up the database order if it was created but IG call failed
            if "order_in_db" in locals():
                try:
                    from app.db.crud import delete_order

                    async with get_db_context() as db:
                        await delete_order(db, order_in_db.id)
                except Exception as cleanup_e:
                    await log_message(
                        "Failed to clean up order after IG error",
                        f"Could not delete order {order_in_db.id} after IG position creation failed: {str(cleanup_e)}",
                        "order",
                        user_id=user.id,
                        extra={
                            "order_id": str(order_in_db.id),
                            "cleanup_error": str(cleanup_e),
                            "original_error": str(e),
                        },
                    )

            await log_message(
                "Failed to create market position",
                f"Error creating market position for instrument {instrument.ig_epic}: {str(e)}",
                "order",
                user_id=user.id,
                extra={
                    "position_request": position_request.model_dump(mode="json"),
                    "user_email": user.email,
                    "instrument_ig_epic": instrument.ig_epic,
                    "order_type": user.settings.order_type.value,
                },
            )
            raise
    else:
        # Use CreateWorkingOrderRequest for limit orders
        order_request = CreateWorkingOrderRequest(
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

        try:
            # Create database order first to get deal_reference
            async with get_db_context() as db:
                order_in_db = await create_order_for_instrument(db, instrument)
                order_request.deal_reference = order_in_db.deal_reference

            # Now create the working order with the deal_reference
            ig_client.create_working_order(order_request)

            await log_message(
                "Order request created",
                f"An order request for instrument with IG Epic {instrument.ig_epic} was made successfully. Order type: {user.settings.order_type.value}. Deal reference: {order_in_db.deal_reference}",
                "order",
                user_id=user.id,
                identifier="order_request_created",
                extra={
                    "order_request": order_request.model_dump(mode="json"),
                    "instrument_ig_epic": instrument.ig_epic,
                    "order_type": user.settings.order_type.value,
                    "deal_reference": order_in_db.deal_reference,
                    "order_id": str(order_in_db.id),
                },
            )

            await confirm_deal_reference_for_order(order_in_db.id)

            return order_in_db

        except Exception as e:
            # Clean up the database order if it was created but IG call failed
            if "order_in_db" in locals():
                try:
                    from app.db.crud import delete_order

                    async with get_db_context() as db:
                        await delete_order(db, order_in_db.id)
                except Exception as cleanup_e:
                    await log_message(
                        "Failed to clean up order after IG error",
                        f"Could not delete order {order_in_db.id} after IG working order creation failed: {str(cleanup_e)}",
                        "order",
                        user_id=user.id,
                        extra={
                            "order_id": str(order_in_db.id),
                            "cleanup_error": str(cleanup_e),
                            "original_error": str(e),
                        },
                    )

            await log_message(
                "Failed to create order",
                f"Error creating working order for instrument {instrument.ig_epic}: {str(e)}",
                "order",
                user_id=user.id,
                extra={
                    "order_request": order_request.model_dump(mode="json"),
                    "user_email": user.email,
                    "instrument_ig_epic": instrument.ig_epic,
                    "order_type": user.settings.order_type.value,
                },
            )
            raise
