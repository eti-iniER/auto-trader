from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class TradingViewAlert(BaseModel):
    market: str = Field(..., description="Market on which the stock trades")
    stock_symbol: str = Field(..., description="Stock symbol that identifies the stock")
    direction: Literal["UP", "DOWN"] = Field(
        ..., description="Direction of the price movement (UP or DOWN)"
    )
    open_price: Decimal = Field(
        ..., description="Price at which the stock opened today"
    )
    atrs: list[Decimal] = Field(
        ...,
        description="Average True Ranges of the stock for the previous ten days",
    )


async def parse_trading_view_alert(alert: str) -> TradingViewAlert:
    parts = alert.split(",")

    if len(parts) != 13:
        raise ValueError("Alert format is incorrect. Expected 13 parts.")

    market, stock_symbol = parts[0].split(":")
    direction = parts[1].strip().upper()
    open_price = Decimal(parts[2])
    atrs = [Decimal(part) for part in parts[3:]]

    return TradingViewAlert(
        market=market.strip(),
        stock_symbol=stock_symbol.strip(),
        direction=direction,
        open_price=open_price,
        atrs=atrs,
    )
