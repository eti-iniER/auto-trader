import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated, List

from app.api.utils.authentication import get_current_user
from app.api.utils.caching import cache_user_data, cache_with_pagination
from app.api.utils.pagination import *
from app.api.utils.pagination import PaginationParams, build_paginated_response
from app.clients.ig.client import IGClient
from app.clients.ig.exceptions import IGAPIError, IGAuthenticationError
from app.db.crud import get_market_and_symbol_by_ig_epic
from app.db.deps import get_db
from app.db.models import User
from app.schemas.positions import Position
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/positions", tags=["positions"])

logger = logging.getLogger(__name__)


@cache_user_data(ttl=60, namespace="ig_positions")
async def get_all_positions_from_ig(user: User, db: AsyncSession) -> List[Position]:
    """
    Fetch all open positions from IG and cache them.
    This function handles the IG API call and data transformation.
    """
    ig_client = IGClient.create_for_user(user)

    ig_response = ig_client.get_positions()
    ig_positions_data = [
        position.model_dump(by_alias=True) for position in ig_response.positions
    ]

    positions = []
    for ig_position_data in ig_positions_data:
        position_data = ig_position_data.get("position", {})
        market_data = ig_position_data.get("market", {})

        deal_id = position_data.get("dealId", "")
        if not deal_id:
            continue  # Skip positions without deal ID

        ig_epic = market_data.get("epic", "")
        direction = position_data.get("direction", "").upper()
        size = int(position_data.get("size", 0))
        open_level = Decimal(str(position_data.get("level", 0.0)))

        # Get market_and_symbol from user's instruments
        market_and_symbol = await get_market_and_symbol_by_ig_epic(db, user.id, ig_epic)

        # Extract current market price
        current_level = None
        if direction == "BUY":
            bid_value = market_data.get("bid")
            if bid_value is not None:
                current_level = Decimal(str(bid_value))
        else:  # SELL
            offer_value = market_data.get("offer")
            if offer_value is not None:
                current_level = Decimal(str(offer_value))

        # Calculate profit/loss
        profit_loss = None
        profit_loss_percentage = None
        if current_level and open_level and size:
            if direction == "BUY":
                profit_loss = (current_level - open_level) * Decimal(str(size))
            else:  # SELL
                profit_loss = (open_level - current_level) * Decimal(str(size))

            if open_level != 0:
                if direction == "BUY":
                    profit_loss_percentage = (
                        (current_level - open_level) / open_level
                    ) * Decimal("100")
                else:  # SELL
                    profit_loss_percentage = (
                        (open_level - current_level) / open_level
                    ) * Decimal("100")

        # Parse creation date
        created_date_str = position_data.get("createdDateUTC")
        try:
            if created_date_str:
                # Handle ISO format with Z suffix or UTC datetime
                if created_date_str.endswith("Z"):
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

        # Extract stop and limit levels
        stop_level_value = position_data.get("stopLevel")
        limit_level_value = position_data.get("limitLevel")
        stop_level = (
            Decimal(str(stop_level_value)) if stop_level_value is not None else None
        )
        limit_level = (
            Decimal(str(limit_level_value)) if limit_level_value is not None else None
        )
        controlled_risk = position_data.get("controlledRisk", False)

        position = Position(
            deal_id=deal_id,
            ig_epic=ig_epic,
            market_and_symbol=market_and_symbol,
            direction=direction,
            size=size,
            open_level=open_level,
            current_level=current_level,
            profit_loss=profit_loss,
            profit_loss_percentage=profit_loss_percentage,
            created_at=created_at,
            stop_level=stop_level,
            limit_level=limit_level,
            controlled_risk=controlled_risk,
        )
        positions.append(position)

    return positions


@router.get("", response_model=PaginatedResponse[Position])
@cache_with_pagination(ttl=30, namespace="positions")
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
