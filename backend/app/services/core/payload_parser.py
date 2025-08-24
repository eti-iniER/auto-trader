import logging
from decimal import Decimal

from app.api.schemas.alert import TradingViewAlert
from app.api.schemas.webhook import WebhookPayload

logger = logging.getLogger(__name__)


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
    parts = message.split(" ")
    logger.debug(f"Extracted parts from message: {parts}")
    atrs = parts[-10:]

    if len(atrs) != 10:
        raise ValueError(
            f"Message format is incorrect. Expected exactly 10 ATR values, got {len(atrs)}."
        )

    try:
        atrs = [Decimal(atr.strip()) for atr in atrs if atr.strip()]
        return atrs
    except (ValueError, TypeError) as e:
        raise ValueError(f"Failed to parse ATRs from message: {e}")
