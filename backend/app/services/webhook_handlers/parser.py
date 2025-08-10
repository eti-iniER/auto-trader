from decimal import Decimal

from app.schemas.alert import TradingViewAlert
from app.schemas.webhook import WebhookPayload


async def parse_webhook_payload_to_trading_view_alert(
    payload: WebhookPayload,
) -> TradingViewAlert:
    """Parse a WebhookPayload into a TradingViewAlert by extracting ATRs from the message field."""

    atrs = await parse_atrs_from_message(payload.message)

    return TradingViewAlert(
        market_and_symbol=payload.market_and_symbol,
        direction=payload.direction,
        message=payload.message,
        secret=payload.secret,
        timestamp=payload.timestamp,
        open_price=payload.open_price,
        stop=payload.stop,
        limit=payload.limit,
        size=payload.size,
        atrs=atrs,
    )


async def parse_atrs_from_message(message: str) -> list[Decimal]:
    """Extract ATRs from the message field."""
    parts = message.split(",")

    if len(parts) < 10:
        raise ValueError(
            "Message format is incorrect. Expected at least 10 ATR values."
        )

    try:
        atrs = [Decimal(part.strip()) for part in parts if part.strip()]
        return atrs[:10]
    except (ValueError, TypeError) as e:
        raise ValueError(f"Failed to parse ATRs from message: {e}")
