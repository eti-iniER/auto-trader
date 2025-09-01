from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import AwareDatetime

from fastapi import Query
from app.db.enums import LogType


class InstrumentFilters:
    """Dependency for instrument-specific filters."""

    def __init__(
        self,
        market_and_symbol: Optional[str] = Query(
            None, description="Filter by market and symbol"
        ),
        ig_epic: Optional[str] = Query(None, description="Filter by IG epic"),
        yahoo_symbol: Optional[str] = Query(None, description="Filter by Yahoo symbol"),
        q: Optional[str] = Query(
            None,
            description="Universal search across market_and_symbol, ig_epic, and yahoo_symbol",
        ),
    ):
        self.market_and_symbol = market_and_symbol
        self.ig_epic = ig_epic
        self.yahoo_symbol = yahoo_symbol
        self.q = q

    def to_dict(self) -> Dict[str, Any]:
        """Convert filters to a dictionary, excluding None values."""
        filters = {}
        if self.market_and_symbol:
            filters["market_and_symbol"] = self.market_and_symbol
        if self.ig_epic:
            filters["ig_epic"] = self.ig_epic
        if self.yahoo_symbol:
            filters["yahoo_symbol"] = self.yahoo_symbol
        if self.q:
            filters["q"] = self.q
        return filters

    def to_query_params(self) -> Dict[str, Any]:
        """Convert filters to query parameters for pagination URLs."""
        return {
            "market_and_symbol": self.market_and_symbol,
            "ig_epic": self.ig_epic,
            "yahoo_symbol": self.yahoo_symbol,
            "q": self.q,
        }


class LogFilterParams:
    """Dependency for log filtering parameters."""

    def __init__(
        self,
        from_date: Optional[datetime] = Query(
            None, description="Filter logs from this date"
        ),
        to_date: Optional[datetime] = Query(
            None, description="Filter logs to this date"
        ),
        log_type: Optional[str] = Query(
            None, description="Filter logs by type", alias="type"
        ),
    ):
        self.from_date = from_date
        self.to_date = to_date
        self.log_type = log_type

    def to_dict(self) -> Dict[str, Any]:
        """Convert filters to FastCRUD filter format."""
        filters = {}

        if self.from_date:
            filters["created_at__gte"] = self.from_date

        if self.to_date:
            filters["created_at__lte"] = self.to_date

        if self.log_type:
            try:
                log_type_enum = LogType(self.log_type)
                filters["type"] = log_type_enum
            except ValueError:
                pass

        return filters
