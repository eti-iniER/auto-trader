from decimal import Decimal
from typing import Literal

from app.clients.ig import IGClient
from app.clients.ig.types import CreateWorkingOrderRequest, GetPricesRequest
from app.config import settings
from app.db.crud import create_order_for_instrument
from app.db.deps import get_db_context
from app.db.models import Instrument, Order, User
from app.services.logging import log_message
from app.tasks import confirm_single_deal_reference


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

    # Handle MARKET orders by getting current price
    effective_limit_price = limit_price

    if user.settings.order_type.value == "MARKET":
        # Get current market price for the instrument
        price_request = GetPricesRequest(
            epic=instrument.ig_epic,
            resolution="SECOND",
            max_points=1,  # Get the most recent price
        )

        try:
            price_response = ig_client.get_prices(price_request)
            if price_response.prices:
                latest_price = price_response.prices[0]
                # Use ask price for BUY orders, bid price for SELL orders
                if direction == "BUY":
                    effective_limit_price = (
                        latest_price.close_price.ask
                        or latest_price.close_price.last_traded
                    )
                else:  # SELL
                    effective_limit_price = (
                        latest_price.close_price.bid
                        or latest_price.close_price.last_traded
                    )

                if effective_limit_price is None:
                    raise ValueError(
                        f"Unable to get current market price for {instrument.ig_epic}"
                    )

                await log_message(
                    "Market order price obtained",
                    f"Retrieved current market price for {instrument.ig_epic}: {effective_limit_price} (direction: {direction})",
                    "order",
                    user_id=user.id,
                    identifier="market_order_price_obtained",
                    extra={
                        "instrument_ig_epic": instrument.ig_epic,
                        "direction": direction,
                        "market_price": str(effective_limit_price),
                        "original_order_type": user.settings.order_type.value,
                    },
                )
            else:
                raise ValueError(f"No price data available for {instrument.ig_epic}")

        except Exception as e:
            await log_message(
                "Failed to get market price",
                f"Error getting current market price for {instrument.ig_epic}: {str(e)}",
                "order",
                user_id=user.id,
                extra={
                    "instrument_ig_epic": instrument.ig_epic,
                    "direction": direction,
                    "original_order_type": user.settings.order_type.value,
                },
            )
            raise

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
        level=effective_limit_price,
        type="LIMIT",
        time_in_force="GOOD_TILL_CANCELLED",
    )

    try:
        ig_client.create_working_order(order_request)

        async with get_db_context() as db:
            order_in_db = await create_order_for_instrument(db, instrument)
            order_request.deal_reference = order_in_db.deal_reference

        await log_message(
            "Order request created",
            f"An order request for instrument with IG Epic {instrument.ig_epic} was made successfully. Order type: {user.settings.order_type.value}. We will monitor the order's status.",
            "order",
            user_id=user.id,
            identifier="order_request_created",
            extra={
                "order_request": order_request.model_dump(mode="json"),
                "instrument_ig_epic": instrument.ig_epic,
                "order_type": user.settings.order_type.value,
                "effective_limit_price": str(effective_limit_price),
            },
        )

        confirm_single_deal_reference.send(str(order_in_db.id))

        return order_in_db

    except Exception as e:
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
                "effective_limit_price": str(effective_limit_price),
            },
        )
        raise
