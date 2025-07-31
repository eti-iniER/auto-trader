from typing import Optional, Dict, Any
from fastapi import Request, Query
from app.schemas.instruments import PaginatedResponse


def build_pagination_urls(
    request: Request,
    offset: int,
    limit: int,
    total_count: int,
    endpoint: str,
    **query_params,
) -> tuple[Optional[str], Optional[str]]:
    """
    Build next and previous URLs for pagination.

    Args:
        request: FastAPI request object
        offset: Current offset
        limit: Items per page
        total_count: Total number of items
        endpoint: API endpoint path (e.g., "/api/v1/instruments/")
        **query_params: Additional query parameters to include

    Returns:
        Tuple of (next_url, previous_url)
    """
    base_url = str(request.base_url).rstrip("/")

    # Build query string from existing params
    query_string_parts = []
    for key, value in query_params.items():
        if value is not None:
            query_string_parts.append(f"{key}={value}")

    # Calculate next URL
    next_url = None
    if offset + limit < total_count:
        next_offset = offset + limit
        next_params = query_string_parts + [f"offset={next_offset}", f"limit={limit}"]
        next_url = f"{base_url}{endpoint}?{'&'.join(next_params)}"

    # Calculate previous URL
    previous_url = None
    if offset > 0:
        prev_offset = max(0, offset - limit)
        prev_params = query_string_parts + [f"offset={prev_offset}", f"limit={limit}"]
        previous_url = f"{base_url}{endpoint}?{'&'.join(prev_params)}"

    return next_url, previous_url


def build_paginated_response(
    request: Request,
    result: Dict[str, Any],
    offset: int,
    limit: int,
    endpoint: str,
    response_class: type,
    **query_params,
) -> PaginatedResponse:
    """
    Build a standardized paginated response.

    Args:
        request: FastAPI request object
        result: Result from FastCRUD get_multi containing 'data' and 'total_count'
        offset: Current offset
        limit: Items per page
        endpoint: API endpoint path
        response_class: Pydantic model class for the response items
        **query_params: Additional query parameters to include in pagination URLs

    Returns:
        PaginatedResponse instance
    """
    next_url, previous_url = build_pagination_urls(
        request=request,
        offset=offset,
        limit=limit,
        total_count=result["total_count"],
        endpoint=endpoint,
        **query_params,
    )

    return PaginatedResponse[response_class](
        count=result["total_count"],
        next=next_url,
        previous=previous_url,
        data=result["data"],
    )


class PaginationParams:
    """Dependency for common pagination parameters."""

    def __init__(
        self,
        offset: int = Query(0, ge=0, description="Number of records to skip"),
        limit: int = Query(
            100, ge=1, le=1000, description="Maximum number of records to return"
        ),
    ):
        self.offset = offset
        self.limit = limit


class SortingParams:
    """Dependency for common sorting parameters."""

    def __init__(
        self,
        sort_by: Optional[str] = Query(None, description="Column to sort by"),
        sort_order: Optional[str] = Query(
            "asc", regex="^(asc|desc)$", description="Sort order"
        ),
    ):
        self.sort_by = sort_by
        self.sort_order = sort_order

    @property
    def sort_columns(self) -> Optional[list[str]]:
        """Return sort columns as a list if sort_by is provided."""
        return [self.sort_by] if self.sort_by else None

    @property
    def sort_orders(self) -> Optional[list[str]]:
        """Return sort orders as a list if sort_by is provided."""
        return [self.sort_order] if self.sort_by else None


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
