from decimal import Decimal

from pydantic import AwareDatetime, BaseModel, Field


class InstrumentSchema(BaseModel):
    market_and_symbol: str = Field(...)
    ig_epic: str = Field(...)
    yahoo_symbol: str = Field(...)
    atr_stop_loss_period: int = Field(...)
    atr_stop_loss_multiple: Decimal = Field(...)
    atr_profit_target_period: int = Field(...)
    atr_profit_multiple: Decimal = Field(...)
    max_position_size: int = Field(...)
    opening_price_multiple: Decimal = Field(...)
    next_dividend_date: AwareDatetime = Field(...)
