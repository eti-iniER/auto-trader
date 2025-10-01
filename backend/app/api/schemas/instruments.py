import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Optional, TypeVar

from pydantic import AwareDatetime, BaseModel, Field, field_validator

T = TypeVar("T")


def ensure_timezone_aware(v: Any) -> datetime:
    """Convert naive datetime to UTC timezone-aware datetime."""
    if v is None:
        return v
    if isinstance(v, datetime):
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v
    return v


class InstrumentBase(BaseModel):
    market_and_symbol: str = Field(..., description="Market and symbol identifier")
    ig_epic: str = Field(..., description="IG trading epic")
    yahoo_symbol: str = Field(..., description="Yahoo Finance symbol")
    atr_stop_loss_period: int = Field(..., description="ATR stop loss period")
    atr_stop_loss_multiple_percentage: Decimal = Field(
        default=Decimal("1.0"), description="ATR stop loss multiple"
    )
    atr_profit_target_period: int = Field(..., description="ATR profit target period")
    atr_profit_multiple_percentage: Decimal = Field(
        default=Decimal("1.0"), description="ATR profit multiple"
    )
    max_position_size: Optional[Decimal] = Field(
        None, description="Maximum position size"
    )
    opening_price_multiple_percentage: Decimal = Field(
        default=Decimal("1.0"), description="Opening price multiple"
    )
    next_dividend_date: Optional[AwareDatetime] = Field(
        None, description="Next dividend date"
    )
    trading_view_price_multiplier: Decimal = Field(
        default=Decimal("1.0"), description="TradingView price multiplier"
    )
    last_alert_received_at: Optional[AwareDatetime] = Field(
        None, description="Timestamp of the last alert received"
    )


class InstrumentCreate(InstrumentBase):
    user_id: uuid.UUID = Field(..., description="User ID of the instrument owner")
    pass


class InstrumentUpdate(BaseModel):
    market_and_symbol: Optional[str] = Field(
        None, description="Market and symbol identifier"
    )
    ig_epic: Optional[str] = Field(None, description="IG trading epic")
    yahoo_symbol: Optional[str] = Field(None, description="Yahoo Finance symbol")
    atr_stop_loss_period: Optional[int] = Field(
        None, description="ATR stop loss period"
    )
    atr_stop_loss_multiple_percentage: Optional[Decimal] = Field(
        None, description="ATR stop loss multiple"
    )
    atr_profit_target_period: Optional[int] = Field(
        None, description="ATR profit target period"
    )
    atr_profit_multiple_percentage: Optional[Decimal] = Field(
        None, description="ATR profit multiple"
    )
    max_position_size: Optional[int] = Field(None, description="Maximum position size")
    opening_price_multiple_percentage: Optional[Decimal] = Field(
        None, description="Opening price multiple"
    )
    next_dividend_date: Optional[AwareDatetime] = Field(
        None, description="Next dividend date"
    )
    trading_view_price_multiplier: Optional[Decimal] = Field(
        None, description="TradingView price multiplier"
    )


class InstrumentRead(InstrumentBase):
    id: uuid.UUID
    created_at: AwareDatetime
    updated_at: AwareDatetime

    @field_validator("created_at", "updated_at", "next_dividend_date", mode="before")
    @classmethod
    def ensure_timezone_aware_validator(cls, v: Any) -> datetime:
        """Ensure datetime fields are timezone-aware, defaulting to UTC."""
        return ensure_timezone_aware(v)

    class Config:
        from_attributes = True


class InstrumentSchema(InstrumentRead):
    """Alias for backward compatibility"""

    pass


class InstrumentUploadResponse(BaseModel):
    """Response model for CSV upload endpoint"""

    message: str = Field(..., description="Success message")
    instruments_created: int = Field(..., description="Number of instruments created")


class DividendFetchResponse(BaseModel):
    """Response model for dividend fetch endpoint"""

    message: str = Field(..., description="Success message")
