import logging

from fastapi import APIRouter, Body

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/trading-view-webhook")
async def trading_view_webhook(alert: str = Body(..., media_type="text/plain")):
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
