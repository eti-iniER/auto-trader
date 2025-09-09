import logging

from app.api.schemas.webhook import WebhookPayload
from app.api.helpers.webhook_payload_parser import parse_webhook_payload
from app.tasks import handle_trading_alert
from fastapi import APIRouter, Request
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhook"])


@router.post("/trading-view-webhook")
async def trading_view_webhook(request: Request):
    """
    Receives TradingView webhook with plaintext body.

    Expects a plaintext request body containing the alert data.
    """

    body = await request.body()
    alert = body.decode()

    received_at = datetime.now(timezone.utc)
    payload = parse_webhook_payload(alert)
    payload.received_at = received_at
    logger.info(f"Parsed payload: {payload}")

    # Send the payload to the actor for processing
    handle_trading_alert.send(payload.model_dump(mode="json"))

    logger.info(f"Received TradingView webhook: {alert}")

    return {
        "status": "success",
        "message": "Webhook received",
        "alert": alert,
    }
