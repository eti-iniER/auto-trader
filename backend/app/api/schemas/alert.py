from decimal import Decimal
from typing import Optional, Literal

from pydantic import AwareDatetime, BaseModel, Field


class TradingViewAlert(BaseModel):
    market_and_symbol: str = Field(
        ..., description="The symbol for which the webhook is triggered"
    )
    direction: Literal["BUY", "SELL"] = Field(
        ..., description="The direction of the trade (buy/sell)"
    )
    message: str = Field(..., description="The message associated with the webhook")
    secret: str = Field(..., description="Secret key for webhook validation")
    timestamp: AwareDatetime = Field(
        ..., description="The timestamp when the webhook was triggered"
    )
    open_price: Optional[Decimal] = Field(
        ...,
        description="Optional open price for the trade",
    )
    atrs: list[Decimal] = Field(
        ...,
        description="Average True Ranges of the stock for the previous ten days",
    )
