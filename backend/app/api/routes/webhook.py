import logging

from app.api.schemas.webhook import WebhookPayload
from app.api.helpers.webhook_payload_parser import parse_webhook_payload
from app.services.trading.handler import handle_alert
from fastapi import APIRouter, BackgroundTasks, Request

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhook"])


@router.post("/trading-view-webhook")
async def trading_view_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Receives TradingView webhook with plaintext body.

    Expects a plaintext request body containing the alert data.
    """

    body = await request.body()
    alert = body.decode()

    payload = parse_webhook_payload(alert)
    logger.info(f"Parsed payload: {payload}")

    background_tasks.add_task(handle_alert, payload)

    logger.info(f"Received TradingView webhook: {alert}")

    return {
        "status": "success",
        "message": "Webhook received",
        "alert": alert,
    }
