"""
Helpers for parsing IG positions data into our Position schema.
"""

import logging
from decimal import Decimal
from typing import List, Optional

from app.api.helpers.ig_utils import parse_ig_datetime
from app.db.crud import get_market_and_symbol_by_ig_epic
from app.db.models import User
from app.api.schemas.positions import Position
from app.clients.ig.client import IGClient
from app.clients.ig.types import GetPricesRequest
from app.clients.ig.exceptions import IGAPIError
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def _calculate_profit_loss(
    direction: str, current_level: Optional[Decimal], open_level: Decimal, size: int
) -> tuple[Optional[Decimal], Optional[Decimal]]:
    """
    Calculate profit/loss and profit/loss percentage for a position.

    Args:
        direction: Position direction (BUY or SELL)
        current_level: Current market price
        open_level: Opening price
        size: Position size

    Returns:
        Tuple of (profit_loss, profit_loss_percentage)
    """
    if not current_level or not open_level or not size:
        return None, None

    # Calculate absolute profit/loss
    if direction == "BUY":
        profit_loss = (current_level - open_level) * Decimal(str(size))
    else:  # SELL
        profit_loss = (open_level - current_level) * Decimal(str(size))

    # Calculate profit/loss percentage
    profit_loss_percentage = None
    if open_level != 0:
        if direction == "BUY":
            profit_loss_percentage = (
                (current_level - open_level) / open_level
            ) * Decimal("100")
        else:  # SELL
            profit_loss_percentage = (
                (open_level - current_level) / open_level
            ) * Decimal("100")

    return profit_loss, profit_loss_percentage


def _extract_current_level(
    direction: str, ig_epic: str, ig_client: IGClient
) -> Optional[Decimal]:
    """
    Extract current market price based on position direction using IG API.

    Args:
        direction: Position direction (BUY or SELL)
        ig_epic: The IG epic identifier for the instrument
        ig_client: IG client instance for API calls

    Returns:
        Current market price as Decimal or None
    """
    try:
        # Get the most recent price data for the instrument
        request = GetPricesRequest(epic=ig_epic, resolution="SECOND", max_points=1)
        response = ig_client.get_prices(request)

        if not response.prices:
            logger.warning(f"No price data returned for epic {ig_epic}")
            return None

        # Get the most recent price snapshot
        latest_price = response.prices[0]

        # Extract the appropriate price based on direction
        if direction == "BUY":
            # For BUY positions, we want the bid price (what we can sell at)
            bid_value = latest_price.close_price.bid
            if bid_value is not None:
                return bid_value
        else:  # SELL
            # For SELL positions, we want the ask price (what we can buy at to close)
            ask_value = latest_price.close_price.ask
            if ask_value is not None:
                return ask_value

        logger.warning(
            f"No suitable price data found for direction {direction} and epic {ig_epic}"
        )
        return None

    except IGAPIError as e:
        logger.error(f"IG API error getting price for epic {ig_epic}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error getting price for epic {ig_epic}: {e}")
        return None


async def parse_ig_position_to_schema(
    ig_position_data: dict, user: User, db: AsyncSession
) -> Optional[Position]:
    """
    Parse a single IG position data object into our Position schema.

    Args:
        ig_position_data: Raw position data from IG API
        user: User object for database lookups
        db: Database session

    Returns:
        Position object or None if parsing fails
    """
    position_data = ig_position_data.get("position", {})
    market_data = ig_position_data.get("market", {})

    deal_id = position_data.get("dealId", "")
    if not deal_id:
        logger.warning("Skipping position without deal ID")
        return None

    ig_epic = market_data.get("epic", "")
    direction = position_data.get("direction", "").upper()
    size = Decimal(position_data.get("size", 0.00))
    open_level = Decimal(str(position_data.get("level", 0.0)))

    # Get market_and_symbol from user's instruments
    market_and_symbol = await get_market_and_symbol_by_ig_epic(db, user.id, ig_epic)

    # Create IG client to get current price
    ig_client = IGClient.create_for_user(user)

    # Extract current market price using IG API
    current_level = _extract_current_level(direction, ig_epic, ig_client)

    # Calculate profit/loss
    profit_loss, profit_loss_percentage = _calculate_profit_loss(
        direction, current_level, open_level, size
    )

    # Parse creation date
    created_at = parse_ig_datetime(position_data.get("createdDateUTC"))

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

    return Position(
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


async def parse_ig_positions_to_schema(
    ig_positions_data: List[dict], user: User, db: AsyncSession
) -> List[Position]:
    """
    Parse a list of IG positions data into our Position schema.

    Args:
        ig_positions_data: List of raw position data from IG API
        user: User object for database lookups
        db: Database session

    Returns:
        List of Position objects
    """
    positions = []

    for ig_position_data in ig_positions_data:
        position = await parse_ig_position_to_schema(ig_position_data, user, db)
        if position:
            positions.append(position)

    return positions
