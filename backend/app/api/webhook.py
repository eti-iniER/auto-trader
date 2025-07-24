import logging

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/trading-view-webhook")
async def trading_view_webhook(request: Request):
    body = await request.body()
    alert = body.decode()

    response = {
        "status": "success",
        "message": "Webhook received",
        "alert": alert,
    }

    logger.info(f"Received TradingView webhook: {alert}")
    logger.debug(f"Webhook body: {body}")
    logger.debug(f"Webhook response: {response}")

    return response
