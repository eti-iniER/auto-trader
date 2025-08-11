from app.db.crud import get_instrument_by_market_and_symbol, get_user_by_webhook_secret
from app.db.deps import get_db_context
from app.schemas.webhook import WebhookPayload
from app.services.core.calculation_helpers import *
from app.services.core.payload_parser import parse_webhook_payload_to_trading_view_alert
from app.services.core.payload_validator import validate_webhook_payload
from app.services.core.trade_executor import create_order
from backend.app.services.logging.helper import log_message


async def handle_alert(payload: WebhookPayload):
    is_valid, error_message = await validate_webhook_payload(payload)

    if not is_valid:
        log_message(
            "Invalid webhook payload received",
            error_message or "Unknown error",
            "error",
            {
                "payload": payload.model_dump(mode="json"),
            },
        )
        return

    log_message(
        "Received valid webhook payload",
        "Alert has been scheduled for processing",
        "alert",
        {
            "payload": payload.model_dump(mode="json"),
        },
    )

    alert = await parse_webhook_payload_to_trading_view_alert(payload)

    async with get_db_context() as db:
        user = await get_user_by_webhook_secret(db, alert.secret)
        instrument = await get_instrument_by_market_and_symbol(
            db, alert.market_and_symbol
        )

    open_price = alert.open_price

    limit_price = calculate_limit_price(
        alert.direction, open_price, instrument.opening_price_multiple_percentage
    )
    bet_size = calculate_bet_size(limit_price, instrument.position_size)
    profit_target_price = calculate_profit_target_price(
        instrument.atr_profit_target_period,
        alert.atrs,
        instrument.atr_profit_multiple_percentage,
    )
    stop_loss_price = calculate_stop_loss_price(
        instrument.atr_stop_loss_period,
        alert.atrs,
        instrument.atr_stop_loss_multiple_percentage,
    )

    await create_order(
        user=user,
        instrument=instrument,
        direction=alert.direction,
        profit_target=profit_target_price,
        limit_price=limit_price,
        stop_loss=stop_loss_price,
        size=bet_size,
    )
