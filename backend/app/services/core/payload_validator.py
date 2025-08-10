from typing import Optional, Tuple

from app.db.crud import get_user_by_webhook_secret
from app.db.deps import get_db_context
from app.db.enums import UserSettingsMode
from app.schemas.webhook import WebhookPayload


async def validate_webhook_payload(
    payload: WebhookPayload,
) -> Tuple[bool, Optional[str]]:
    async with get_db_context() as db:
        user = await get_user_by_webhook_secret(db, payload.secret)

        if user.settings.mode == UserSettingsMode.DEMO:
            if payload.secret != user.settings.demo_webhook_secret:
                return (
                    False,
                    "MISMATCHED_DEMO_WEBHOOK_SECRET",
                )
        elif user.settings.mode == UserSettingsMode.LIVE:
            if payload.secret != user.settings.live_webhook_secret:
                return (
                    False,
                    "MISMATCHED_LIVE_WEBHOOK_SECRET",
                )

    return True, None
