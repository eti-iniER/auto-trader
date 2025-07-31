from decimal import Decimal
from datetime import date, datetime, timezone
from typing import Optional, List, Generic, TypeVar, Any
import uuid

from pydantic import BaseModel, Field, ConfigDict, AwareDatetime, field_validator

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


class PaginatedResponse(BaseModel, Generic[T]):
    count: int = Field(..., description="Total number of items")
    next: Optional[str] = Field(None, description="URL for next page")
    previous: Optional[str] = Field(None, description="URL for previous page")
    data: List[T] = Field(..., description="List of items for current page")


import uuid

from pydantic import BaseModel, Field, AwareDatetime


class InstrumentBase(BaseModel):
    market_and_symbol: str = Field(..., description="Market and symbol identifier")
    ig_epic: str = Field(..., description="IG trading epic")
    yahoo_symbol: str = Field(..., description="Yahoo Finance symbol")
    atr_stop_loss_period: int = Field(..., description="ATR stop loss period")
    atr_stop_loss_multiple: Decimal = Field(
        default=Decimal("1.0"), description="ATR stop loss multiple"
    )
    atr_profit_target_period: int = Field(..., description="ATR profit target period")
    atr_profit_multiple: Decimal = Field(
        default=Decimal("1.0"), description="ATR profit multiple"
    )
    position_size: int = Field(default=1, description="Position size")
    max_position_size: Optional[int] = Field(None, description="Maximum position size")
    opening_price_multiple: Decimal = Field(
        default=Decimal("1.0"), description="Opening price multiple"
    )
    next_dividend_date: Optional[AwareDatetime] = Field(
        None, description="Next dividend date"
    )


class InstrumentCreate(InstrumentBase):
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
    atr_stop_loss_multiple: Optional[Decimal] = Field(
        None, description="ATR stop loss multiple"
    )
    atr_profit_target_period: Optional[int] = Field(
        None, description="ATR profit target period"
    )
    atr_profit_multiple: Optional[Decimal] = Field(
        None, description="ATR profit multiple"
    )
    position_size: Optional[int] = Field(None, description="Position size")
    max_position_size: Optional[int] = Field(None, description="Maximum position size")
    opening_price_multiple: Optional[Decimal] = Field(
        None, description="Opening price multiple"
    )
    next_dividend_date: Optional[AwareDatetime] = Field(
        None, description="Next dividend date"
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
