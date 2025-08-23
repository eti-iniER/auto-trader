"""
Helpers for parsing IG positions data into our Position schema.
"""

import logging
from decimal import Decimal
from typing import List, Optional

from app.api.helpers.ig_utils import parse_ig_datetime
from app.db.crud import get_market_and_symbol_by_ig_epic
from app.db.models import User
from app.schemas.positions import Position
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


def _extract_current_level(direction: str, market_data: dict) -> Optional[Decimal]:
    """
    Extract current market price based on position direction.

    Args:
        direction: Position direction (BUY or SELL)
        market_data: Market data from IG API

    Returns:
        Current market price as Decimal or None
    """
    if direction == "BUY":
        bid_value = market_data.get("bid")
        if bid_value is not None:
            return Decimal(str(bid_value))
    else:  # SELL
        offer_value = market_data.get("offer")
        if offer_value is not None:
            return Decimal(str(offer_value))

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

    # Extract current market price
    current_level = _extract_current_level(direction, market_data)

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
