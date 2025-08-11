from app.db.models import User, Instrument
from app.clients.ig.types import CreateWorkingOrderRequest
from app.clients.ig import IGClient
from decimal import Decimal
from app.config import settings
from typing import Literal
from backend.app.services.logging.helper import log_message


async def create_order(
    user: User,
    instrument: Instrument,
    direction: Literal["BUY", "SELL"],
    profit_target: Decimal,
    limit_price: Decimal,
    stop_loss: Decimal,
    size: int,
) -> None:
    ig_client = IGClient.create_for_user(user)

    order_request = CreateWorkingOrderRequest(
        currency_code=settings.DEFAULT_CURRENCY_CODE,
        direction=direction,
        stopLevel=stop_loss,
        limitLevel=profit_target,
        epic=instrument.ig_epic,
        expiry="DEC-27",  # Expiry date gotten from making orders via IG's dashboard when set to "Good till cancelled"
        force_open=False,
        size=size,
        good_till_date=None,
        guaranteed_stop=False,
        level=limit_price,
        type=user.settings.order_type.value,
        time_in_force="GOOD_TILL_CANCELLED",
    )

    try:
        ig_client.create_working_order(order_request)
        await log_message(
            "Order created",
            f"Order for user [{user.email}] on instrument {instrument.ig_epic} created successfully.",
            "order",
            extra={
                "order_request": order_request.model_dump(mode="json"),
                "user_email": user.email,
                "instrument_ig_epic": instrument.ig_epic,
            },
        )
    except Exception as e:
        await log_message(
            "Failed to create order",
            f"Error creating order for user [{user.email}] on instrument {instrument.ig_epic}: {str(e)}",
            "order",
            extra={
                "order_request": order_request.model_dump(mode="json"),
                "user_email": user.email,
                "instrument_ig_epic": instrument.ig_epic,
            },
        )
