from decimal import Decimal
from typing import Literal

from app.clients.ig import IGClient
from app.clients.ig.types import CreateWorkingOrderRequest
from app.config import settings
from app.db.crud import create_order_for_instrument
from app.db.deps import get_db_context
from app.db.models import Instrument, User
from app.services.logging import log_message


async def create_order(
    user: User,
    instrument: Instrument,
    direction: Literal["BUY", "SELL"],
    profit_target: Decimal,
    limit_price: Decimal,
    stop_loss: Decimal,
    size: Decimal,
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
        async with get_db_context() as db:
            order_in_db = await create_order_for_instrument(db, instrument)
            order_request.deal_reference = order_in_db.deal_reference

        ig_client.create_working_order(order_request)

        await log_message(
            "Order request created",
            f"An order request for instrument with IG Epic {instrument.ig_epic} was made successfully. We will monitor and confirm the order's acceptance shortly.",
            "order",
            user_id=user.id,
            identifier="order_request_created",
            extra={
                "order_request": order_request.model_dump(mode="json"),
                "instrument_ig_epic": instrument.ig_epic,
            },
        )
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
            },
        )
