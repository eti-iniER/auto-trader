from typing import Any, Dict, Optional

from fastapi import Query


class InstrumentFilters:
    """Dependency for instrument-specific filters."""

    def __init__(
        self,
        market_and_symbol: Optional[str] = Query(
            None, description="Filter by market and symbol"
        ),
        ig_epic: Optional[str] = Query(None, description="Filter by IG epic"),
        yahoo_symbol: Optional[str] = Query(None, description="Filter by Yahoo symbol"),
    ):
        self.market_and_symbol = market_and_symbol
        self.ig_epic = ig_epic
        self.yahoo_symbol = yahoo_symbol

    def to_dict(self) -> Dict[str, Any]:
        """Convert filters to a dictionary, excluding None values."""
        filters = {}
        if self.market_and_symbol:
            filters["market_and_symbol"] = self.market_and_symbol
        if self.ig_epic:
            filters["ig_epic"] = self.ig_epic
        if self.yahoo_symbol:
            filters["yahoo_symbol"] = self.yahoo_symbol
        return filters

    def to_query_params(self) -> Dict[str, Any]:
        """Convert filters to query parameters for pagination URLs."""
        return {
            "market_and_symbol": self.market_and_symbol,
            "ig_epic": self.ig_epic,
            "yahoo_symbol": self.yahoo_symbol,
        }
