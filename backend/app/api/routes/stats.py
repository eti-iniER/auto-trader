import logging
from typing import Annotated

from app.api.utils.authentication import get_current_user
from app.api.utils.caching import cache_user_data
from app.clients.ig.client import IGClient
from app.clients.ig.exceptions import IGAPIError, IGAuthenticationError
from app.db.deps import get_db
from app.db.models import User
from app.api.schemas.stats import UserQuickStatsResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/stats", tags=["stats"])

logger = logging.getLogger(__name__)


@cache_user_data(ttl=0, namespace="ig_user_stats")
async def get_user_quick_stats_from_ig(user: User) -> UserQuickStatsResponse:
    """
    Fetch user quick stats from IG and cache them.
    This function handles the IG API call and returns the stats.
    """
    try:
        ig_client = await IGClient.create_for_user(user)

        ig_stats = ig_client.get_user_quick_stats()

        return UserQuickStatsResponse(
            open_positions_count=ig_stats.open_positions_count,
            open_orders_count=ig_stats.open_orders_count,
            recent_activities=ig_stats.recent_activities,
            stats_timestamp=ig_stats.stats_timestamp,
        )

    except IGAuthenticationError as e:
        logger.error(f"IG authentication failed for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to authenticate with IG API. Please check your credentials.",
        )
    except IGAPIError as e:
        logger.error(f"IG API error for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"IG API error: {e.message}",
        )
    except Exception as e:
        logger.error(f"Unexpected error getting stats for user {user.id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user stats",
        )


@router.get("", response_model=UserQuickStatsResponse)
async def get_user_stats(
    user: Annotated[User, Depends(get_current_user)],
) -> UserQuickStatsResponse:
    """
    Get quick stats for the current user including:
    - Number of open positions
    - Number of open working orders
    - Recent activities from the last day

    This endpoint combines multiple IG API calls to provide a summary dashboard view.
    Results are cached for 30 seconds to improve performance for frequent requests.
    """
    return await get_user_quick_stats_from_ig(user)
