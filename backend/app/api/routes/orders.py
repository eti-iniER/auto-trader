import logging
from typing import Annotated, List

from app.api.helpers.orders_parser import parse_ig_orders_to_schema
from app.api.schemas.orders import Order
from app.api.schemas.generic import SimpleResponseSchema
from app.api.utils.authentication import get_current_user
from app.api.utils.caching import cache_user_data, cache_with_pagination
from app.api.utils.pagination import *
from app.api.utils.pagination import PaginationParams, build_paginated_response
from app.clients.ig.client import IGClient
from app.clients.ig.exceptions import IGAPIError, IGAuthenticationError
from app.clients.ig.types import DeleteWorkingOrderRequest
from app.db.models import User
from fastapi import APIRouter, Depends, HTTPException, Request, status

router = APIRouter(prefix="/orders", tags=["orders"])

logger = logging.getLogger(__name__)


@cache_user_data(ttl=60, namespace="ig_orders")
async def get_all_orders_from_ig(user: User) -> List[Order]:
    """
    Fetch all working orders from IG and cache them.
    This function handles the IG API call and data transformation.
    """
    ig_client = await IGClient.create_for_user(user)
    ig_response = await ig_client.get_working_orders()
    ig_orders_data = [
        order.model_dump(by_alias=True) for order in ig_response.working_orders
    ]

    orders = parse_ig_orders_to_schema(ig_orders_data)
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


@router.delete("/{deal_id}", response_model=SimpleResponseSchema)
async def delete_working_order(
    deal_id: str,
    user: Annotated[User, Depends(get_current_user)],
) -> SimpleResponseSchema:
    """
    Delete/cancel a working order by its deal ID.

    This endpoint calls the IG API to cancel an active working order identified by the deal ID.

    Args:
        deal_id (str): The deal ID of the working order to cancel
        user (User): The authenticated user

    Returns:
        SimpleResponseSchema: Success message with deal reference
    """
    try:
        # Create delete working order request
        delete_request = DeleteWorkingOrderRequest(deal_id=deal_id)

        # Call IG API to delete the working order
        ig_client = await IGClient.create_for_user(user)
        delete_response = await ig_client.delete_working_order(delete_request)

        logger.info(
            f"Working order {deal_id} deleted successfully for user {user.id}. Deal reference: {delete_response.deal_reference}"
        )

        return SimpleResponseSchema(
            message=f"Working order cancelled successfully. Deal reference: {delete_response.deal_reference}"
        )

    except IGAuthenticationError as e:
        logger.error(f"IG authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to authenticate with IG: {str(e)}",
        )
    except IGAPIError as e:
        logger.error(f"IG API error deleting working order {deal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"IG API error: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting working order {deal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete working order: {str(e)}",
        )
