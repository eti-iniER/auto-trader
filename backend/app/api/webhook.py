from fastapi import APIRouter, Request

router = APIRouter()


@router.post("/trading-view-webhook")
async def trading_view_webhook(request: Request):
    body = await request.body()
    alert = body.decode()

    return {
        "status": "success",
        "message": "Webhook received",
        "alert": alert,
    }
