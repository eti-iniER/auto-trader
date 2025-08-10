import logging

from app.schemas.webhook import WebhookPayload
from fastapi import APIRouter, Body

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhook"])


@router.post("/trading-view-webhook")
async def trading_view_webhook(alert: WebhookPayload):
    """
    Receives TradingView webhook with plaintext body.

    Expects a plaintext request body containing the alert data.
    """

    response = {
        "status": "success",
        "message": "Webhook received",
        "alert": alert,
    }

    logger.info(f"Received TradingView webhook: {alert}")
    logger.debug(f"Webhook response: {response}")

    return response
