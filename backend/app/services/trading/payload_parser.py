import logging
from decimal import Decimal
from typing import Literal

from app.api.schemas.alert import TradingViewAlert
from app.api.schemas.webhook import WebhookPayload

logger = logging.getLogger(__name__)


async def parse_webhook_payload_to_trading_view_alert(
    payload: WebhookPayload,
) -> TradingViewAlert:
    """Parse a WebhookPayload into a TradingViewAlert by extracting ATRs from the message field."""

    parsed = parse_message_fields(payload.message)

    return TradingViewAlert(
        market_and_symbol=parsed["market_and_symbol"],
        direction=parsed["direction"],
        message=payload.message,
        secret=payload.secret,
        timestamp=payload.timestamp,
        open_price=parsed["open_price"],
        stop=payload.stop,
        limit=payload.limit,
        size=payload.size,
        atrs=parsed["atrs"],
    )


def parse_message_fields(message: str):
    """Extract open price, direction, and ATRs from the message field."""
    parts = message.split(" ")
    logger.debug(f"Extracted parts from message: {parts}")
    if len(parts) < 13:
        raise ValueError(
            "Message format is incorrect. Expected at least 13 parts (direction, open price, 10 ATRs, etc.)"
        )

    # Market and symbol
    market_and_symbol = parts[0].strip().upper()

    # Direction
    direction_raw = parts[1].strip().upper()
    direction = "SELL" if direction_raw == "UP" else "BUY"

    # Open price
    try:
        open_price = Decimal(parts[2].strip())
    except (ValueError, TypeError) as e:
        raise ValueError(f"Failed to parse open price from message: {e}")

    # ATRs
    atrs_raw = parts[-10:]
    if len(atrs_raw) != 10:
        raise ValueError(
            f"Message format is incorrect. Expected exactly 10 ATR values, got {len(atrs_raw)}."
        )
    try:
        atrs = [Decimal(atr.strip()) for atr in atrs_raw if atr.strip()]
    except (ValueError, TypeError) as e:
        raise ValueError(f"Failed to parse ATRs from message: {e}")

    return {
        "direction": direction,
        "open_price": open_price,
        "atrs": atrs,
        "market_and_symbol": market_and_symbol,
    }
