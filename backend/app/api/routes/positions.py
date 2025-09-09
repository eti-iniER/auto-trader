import logging
from typing import Annotated, List

from app.api.helpers.positions_parser import parse_ig_positions_to_schema
from app.api.utils.authentication import get_current_user
from app.api.utils.caching import cache_user_data, cache_with_pagination
from app.api.utils.pagination import *
from app.api.utils.pagination import PaginationParams, build_paginated_response
from app.clients.ig.client import IGClient
from app.clients.ig.exceptions import IGAPIError, IGAuthenticationError
from app.clients.ig.types import DeletePositionRequest
from app.db.deps import get_db
from app.db.models import User
from app.api.schemas.positions import Position
from app.api.schemas.generic import SimpleResponseSchema
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/positions", tags=["positions"])

logger = logging.getLogger(__name__)


@cache_user_data(ttl=10, namespace="ig_positions")
async def get_all_positions_from_ig(user: User, db: AsyncSession) -> List[Position]:
    """
    Fetch all open positions from IG and cache them.
    This function handles the IG API call and data transformation.
    """
    ig_client = await IGClient.create_for_user(user)
    ig_response = await ig_client.get_positions()

    positions = await parse_ig_positions_to_schema(ig_response.positions, user, db)
    return positions


@router.get("", response_model=PaginatedResponse[Position])
@cache_with_pagination(ttl=10, namespace="positions")
async def list_positions(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    pagination: Annotated[PaginationParams, Depends()],
    user: Annotated[User, Depends(get_current_user)],
) -> PaginatedResponse[Position]:
    """
    Get a list of open positions from IG with pagination.

    This endpoint retrieves all open positions from IG, transforms them to our schema,
    and applies pagination. Both the raw IG data and paginated results are cached.

    Returns:
        PaginatedResponse[Position]: Contains 'data' (list of positions), 'count', 'next', and 'previous' URLs
    """
    try:
        all_positions = await get_all_positions_from_ig(user, db)

        total_count = len(all_positions)
        start_index = pagination.offset
        end_index = start_index + pagination.limit
        paginated_positions = all_positions[start_index:end_index]

        result = {"data": paginated_positions, "total_count": total_count}

        return build_paginated_response(
            request=request,
            result=result,
            offset=pagination.offset,
            limit=pagination.limit,
            endpoint="/api/v1/positions/",
            response_class=Position,
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
        logger.error(f"Unexpected error retrieving positions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve positions: {str(e)}",
        )


@router.delete("/{deal_id}", response_model=SimpleResponseSchema)
async def delete_position(
    deal_id: str,
    user: Annotated[User, Depends(get_current_user)],
) -> SimpleResponseSchema:
    """
    Delete/close a position by its deal ID.

    This endpoint calls the IG API to close an open position identified by the deal ID.

    Args:
        deal_id (str): The deal ID of the position to close
        user (User): The authenticated user

    Returns:
        SimpleResponseSchema: Success message with deal reference
    """
    try:
        # Create delete position request
        delete_request = DeletePositionRequest(deal_id=deal_id)

        # Call IG API to delete the position
        ig_client = await IGClient.create_for_user(user)
        delete_response = await ig_client.delete_position(delete_request)

        logger.info(
            f"Position {deal_id} deleted successfully for user {user.id}. Deal reference: {delete_response.deal_reference}"
        )

        return SimpleResponseSchema(
            message=f"Position closed successfully. Deal reference: {delete_response.deal_reference}"
        )

    except IGAuthenticationError as e:
        logger.error(f"IG authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to authenticate with IG: {str(e)}",
        )
    except IGAPIError as e:
        logger.error(f"IG API error deleting position {deal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"IG API error: {str(e)}",
        )
    except Exception as e:
        logger.error(f"Unexpected error deleting position {deal_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete position: {str(e)}",
        )
