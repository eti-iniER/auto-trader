from decimal import Decimal
from typing import Optional

from pydantic import AwareDatetime, BaseModel, Field


class WebhookPayload(BaseModel):
    market_and_symbol: str = Field(
        ..., description="The symbol for which the webhook is triggered", alias="symbol"
    )
    direction: str = Field(..., description="The direction of the trade (buy/sell)")
    message: str = Field(..., description="The message associated with the webhook")
    secret: str = Field(..., description="Secret key for webhook validation")
    timestamp: AwareDatetime = Field(
        ..., description="The timestamp when the webhook was triggered"
    )
    open_price: Optional[Decimal] = Field(
        ..., description="Optional open price for the trade", alias="price"
    )
    stop: Optional[Decimal] = Field(
        None, description="Optional stop loss price for the trade"
    )
    limit: Optional[Decimal] = Field(
        None, description="Optional take profit price for the trade"
    )
    size: Optional[Decimal] = Field(
        None, description="Optional size of the trade in GBP"
    )

    class Config:
        populate_by_name = True
