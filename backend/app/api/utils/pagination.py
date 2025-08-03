from typing import Any, Dict, Generic, List, Optional, TypeVar

from fastapi import Query, Request
from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    count: int = Field(..., description="Total number of items")
    next: Optional[str] = Field(None, description="URL for next page")
    previous: Optional[str] = Field(None, description="URL for previous page")
    results: List[T] = Field(..., description="List of items for current page")


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

    query_string_parts = []
    for key, value in query_params.items():
        if value is not None:
            query_string_parts.append(f"{key}={value}")

    next_url = None
    if offset + limit < total_count:
        next_offset = offset + limit
        next_params = query_string_parts + [f"offset={next_offset}", f"limit={limit}"]
        next_url = f"{base_url}{endpoint}?{'&'.join(next_params)}"

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
        results=result["data"],
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
