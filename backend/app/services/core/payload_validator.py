from datetime import datetime, timezone, date
from typing import Optional, Tuple

from app.db.crud import get_user_by_webhook_secret, get_instrument_by_market_and_symbol
from app.db.deps import get_db_context
from app.db.enums import UserSettingsMode
from app.schemas.webhook import WebhookPayload
from app.services.logging import log_message


async def validate_webhook_payload(
    payload: WebhookPayload,
) -> Tuple[bool, Optional[str]]:
    async with get_db_context() as db:
        user = await get_user_by_webhook_secret(db, payload.secret)

        # Validate webhook secret
        if user.settings.mode == UserSettingsMode.DEMO:
            if payload.secret != user.settings.demo_webhook_secret:
                await log_message(
                    "Mismatched demo webhook secret",
                    "Alert has been rejected due to mismatched demo webhook secret",
                    "alert",
                    user.id,
                    {
                        "payload": payload.model_dump(mode="json"),
                        "expected_secret": user.settings.demo_webhook_secret,
                        "received_secret": payload.secret,
                    },
                )
                return (
                    False,
                    "MISMATCHED_DEMO_WEBHOOK_SECRET",
                )
        elif user.settings.mode == UserSettingsMode.LIVE:
            if payload.secret != user.settings.live_webhook_secret:
                await log_message(
                    "Mismatched live webhook secret",
                    "Alert has been rejected due to mismatched live webhook secret",
                    "alert",
                    user.id,
                    {
                        "payload": payload.model_dump(mode="json"),
                        "expected_secret": user.settings.live_webhook_secret,
                        "received_secret": payload.secret,
                    },
                )
                return (
                    False,
                    "MISMATCHED_LIVE_WEBHOOK_SECRET",
                )

        # Validate payload age
        payload_age = datetime.now(timezone.utc) - payload.timestamp

        if (
            int(payload_age.total_seconds())
            > user.settings.maximum_alert_age_in_seconds
            and user.settings.enforce_maximum_alert_age_in_seconds
        ):
            await log_message(
                "Maximum alert age exceeded",
                "Alert has been rejected due to exceeding maximum age",
                "alert",
                user.id,
                {
                    "payload": payload.model_dump(mode="json"),
                    "maximum_alert_age_in_seconds": user.settings.maximum_alert_age_in_seconds,
                    "payload_age_seconds": int(payload_age.total_seconds()),
                },
            )
            return (
                False,
                "MAX_ALERT_AGE_EXCEEDED",
            )

        # Validate market and symbol
        instrument = await get_instrument_by_market_and_symbol(
            db, payload.market_and_symbol
        )
        if not instrument:
            await log_message(
                "Instrument not found",
                "Alert has been rejected due to missing or incorrect instrument",
                "alert",
                user.id,
                {
                    "payload": payload.model_dump(mode="json"),
                    "market_and_symbol": payload.market_and_symbol,
                },
            )
            return False, "INSTRUMENT_NOT_FOUND"

        # Validate next dividend date
        if instrument.next_dividend_date.date() == date.today():
            await log_message(
                "Alert received on dividend date",
                "Alert has been ignored due to being received on the dividend date",
                "alert",
                user.id,
                {
                    "payload": payload.model_dump(mode="json"),
                    "dividend_date": instrument.next_dividend_date.isoformat(),
                },
            )
            return False, "ALERT_ON_DIVIDEND_DATE"

    return True, None
