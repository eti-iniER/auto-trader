from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DividendInfo(BaseModel):
    """Information about dividend for a stock."""

    symbol: str
    next_dividend_date: Optional[datetime]
    dividend_rate: Optional[float]
    dividend_yield: Optional[float]
    ex_dividend_date: Optional[datetime]
    pay_date: Optional[datetime]


class StockInfo(BaseModel):
    """Basic stock information."""

    symbol: str
    name: Optional[str]
    sector: Optional[str]
    industry: Optional[str]
    market_cap: Optional[float]
    current_price: Optional[float]
