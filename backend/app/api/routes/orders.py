import logging
from datetime import datetime, timezone
from typing import Annotated, List

from app.api.utils.authentication import get_current_user
from app.api.utils.caching import cache_user_data, cache_with_pagination
from app.api.utils.pagination import *
from app.api.utils.pagination import PaginationParams, build_paginated_response
from app.clients.ig.client import IGClient
from app.clients.ig.exceptions import IGAPIError, IGAuthenticationError
from app.db.models import User
from app.schemas.orders import Order
from fastapi import APIRouter, Depends, HTTPException, Request, status

router = APIRouter(prefix="/orders", tags=["orders"])

logger = logging.getLogger(__name__)


@cache_user_data(ttl=60, namespace="ig_orders")
async def get_all_orders_from_ig(user: User) -> List[Order]:
    """
    Fetch all working orders from IG and cache them.
    This function handles the IG API call and data transformation.
    """
    ig_client = IGClient.create_for_user(user)

    ig_response = ig_client.get_working_orders()
    ig_orders_data = [
        order.model_dump(by_alias=True) for order in ig_response.working_orders
    ]

    orders = []
    for ig_order in ig_orders_data:
        working_order_data = ig_order.get("workingOrderData", {})
        market_data = ig_order.get("marketData", {})

        deal_id = working_order_data.get("dealId", "")
        if not deal_id:
            continue  # Skip orders without deal ID

        ig_epic = working_order_data.get("epic", market_data.get("epic", ""))
        direction = working_order_data.get("direction", "").upper()
        order_type = working_order_data.get("orderType", "")
        size = working_order_data.get("orderSize", 0)

        created_date_str = working_order_data.get("createdDateUTC")
        try:
            if created_date_str:
                # Parse the UTC datetime and make it timezone-aware
                if created_date_str.endswith("Z"):
                    # Handle ISO format with Z suffix
                    created_at = datetime.fromisoformat(
                        created_date_str.replace("Z", "+00:00")
                    )
                else:
                    # Handle UTC datetime without timezone info
                    naive_dt = datetime.fromisoformat(created_date_str)
                    created_at = naive_dt.replace(tzinfo=timezone.utc)
            else:
                created_at = datetime.now(timezone.utc)
        except (ValueError, AttributeError):
            created_at = datetime.now(timezone.utc)

        order_level = working_order_data.get("orderLevel", 0.0)
        stop_distance = working_order_data.get("stopDistance")
        limit_distance = working_order_data.get("limitDistance")

        stop_level = None
        profit_level = None

        if stop_distance and order_level:
            if direction == "BUY":
                stop_level = order_level - stop_distance
            else:  # SELL
                stop_level = order_level + stop_distance

        if limit_distance and order_level:
            if direction == "BUY":
                profit_level = order_level + limit_distance
            else:
                profit_level = order_level - limit_distance

        order = Order(
            deal_id=deal_id,
            ig_epic=ig_epic,
            direction=direction,
            type=order_type,
            size=size,
            created_at=created_at,
            stop_level=stop_level,
            profit_level=profit_level,
        )
        orders.append(order)

    return orders


@router.get("", response_model=PaginatedResponse[Order])
@cache_with_pagination(ttl=30, namespace="orders")
async def list_orders(
    request: Request,
    pagination: Annotated[PaginationParams, Depends()],
    user: Annotated[User, Depends(get_current_user)],
) -> PaginatedResponse[Order]:
    """
    Get a list of working orders from IG with pagination.

    This endpoint retrieves all working orders from IG, transforms them to our schema,
    and applies pagination. Both the raw IG data and paginated results are cached.

    Returns:
        PaginatedOrdersResponse: Contains 'data' (list of orders), 'count', 'next', and 'previous' URLs
    """
    try:
        all_orders = await get_all_orders_from_ig(user)

        total_count = len(all_orders)
        start_index = pagination.offset
        end_index = start_index + pagination.limit
        paginated_orders = all_orders[start_index:end_index]

        result = {"data": paginated_orders, "total_count": total_count}

        return build_paginated_response(
            request=request,
            result=result,
            offset=pagination.offset,
            limit=pagination.limit,
            endpoint="/api/v1/orders/",
            response_class=Order,
        )

    except IGAuthenticationError as e:
        logger.error(f"IG authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to authenticate with IG: {str(e)}",
        )
    except IGAPIError as e:
        logger.error(f"IG API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"IG API error: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving orders: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve orders: {str(e)}",
        )
