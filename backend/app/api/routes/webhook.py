import logging

from app.schemas.webhook import WebhookPayload
from app.services.core.handler import handle_alert
from fastapi import APIRouter, Body, BackgroundTasks

logger = logging.getLogger(__name__)

router = APIRouter(tags=["webhook"])


@router.post("/trading-view-webhook")
async def trading_view_webhook(
    alert: WebhookPayload, background_tasks: BackgroundTasks
):
    """
    Receives TradingView webhook with plaintext body.

    Expects a plaintext request body containing the alert data.
    """

    response = {
        "status": "success",
        "message": "Webhook received",
    }

    background_tasks.add_task(handle_alert, alert)

    logger.info(f"Received TradingView webhook: {alert}")
    logger.debug(f"Webhook response: {response}")

    return response
