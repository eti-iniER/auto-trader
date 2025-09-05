from app.api.schemas.webhook import WebhookPayload

EXAMPLE = "2025-09-05T08:00:00+0100 Ak6dpmB5YWSlFUs3ac56nepuufP5vdsf LSE_DLY:IFX UP 869.604 2.04 11.127 13.152 14.143 14.775 15.226 15.571 15.841 16.055 16.224"


def parse_webhook_payload(payload: str) -> WebhookPayload:
    parts = payload.strip().split(" ", 2)

    if len(parts) < 3:
        raise ValueError("Invalid payload format")

    timestamp, secret, message = parts

    return WebhookPayload(
        timestamp=timestamp.strip(), secret=secret.strip(), message=message.strip()
    )
