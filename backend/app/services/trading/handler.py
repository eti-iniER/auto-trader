from app.api.schemas.instruments import InstrumentRead
from app.api.schemas.webhook import WebhookPayload
from app.db.crud import get_instrument_by_market_and_symbol, get_user_by_webhook_secret
from app.db.deps import get_db_context
from app.services.logging import log_message
from app.services.trading.calculation_helpers import *
from app.services.trading.payload_parser import (
    parse_webhook_payload_to_trading_view_alert,
)
from app.services.trading.payload_validator import validate_webhook_payload
from app.services.trading.price_normalizer import normalize_prices
from app.services.trading.trade_executor import create_order


async def handle_alert(payload: WebhookPayload):
    is_valid, _ = await validate_webhook_payload(payload)

    if not is_valid:
        # the validator already logs the error
        return

    raw_alert = await parse_webhook_payload_to_trading_view_alert(payload)

    async with get_db_context() as db:
        user = await get_user_by_webhook_secret(db, payload.secret)
        instrument = await get_instrument_by_market_and_symbol(
            db, raw_alert.market_and_symbol, user
        )

    alert = await normalize_prices(raw_alert, instrument)

    await log_message(
        "Received valid webhook payload",
        "Alert has been scheduled for processing",
        "alert",
        user.id,
        {
            "payload": payload.model_dump(mode="json"),
        },
    )

    await log_message(
        "Parsed alert from webhook payload",
        "Successfully parsed TradingView alert from webhook payload",
        "alert",
        user.id,
        {
            "alert": alert.model_dump(mode="json"),
        },
    )

    open_price = alert.open_price

    try:
        limit_price = calculate_limit_price(
            alert.direction, open_price, instrument.opening_price_multiple_percentage
        )
        bet_size = calculate_bet_size(limit_price, instrument.max_position_size)
        profit_target_price = calculate_profit_target_price(
            instrument.atr_profit_target_period,
            alert.atrs,
            instrument.atr_profit_multiple_percentage,
        )
        stop_loss_distance = calculate_stop_loss_distance(
            instrument.atr_stop_loss_period,
            alert.atrs,
            instrument.atr_stop_loss_multiple_percentage,
        )
    except Exception as e:
        await log_message(
            "Error calculating trade parameters",
            f"Failed to calculate trade parameters: {str(e)}",
            "error",
            user.id,
            {
                "alert": alert.model_dump(mode="json"),
                "instrument": InstrumentRead.model_validate(instrument).model_dump(
                    mode="json"
                ),
            },
        )
        return

    await create_order(
        user=user,
        instrument=instrument,
        direction=alert.direction,
        limit_distance=profit_target_price,
        limit_price=limit_price,
        stop_loss_distance=stop_loss_distance,
        size=bet_size,
    )
