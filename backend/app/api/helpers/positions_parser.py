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
from app.clients.ig.types import PositionData
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


def _calculate_profit_loss_from_net_change(
    direction: str, net_change: Optional[Decimal], size: int, open_level: Decimal
) -> tuple[Optional[Decimal], Optional[Decimal]]:
    """
    Calculate profit/loss and profit/loss percentage using the netChange from market data.

    Args:
        direction: Position direction (BUY or SELL)
        net_change: Net change from market data (price change from opening level)
        size: Position size
        open_level: Opening price

    Returns:
        Tuple of (profit_loss, profit_loss_percentage)
    """
    if net_change is None or not size or not open_level:
        return None, None

    # Calculate absolute profit/loss using net change and position size
    # For BUY: profit when net_change is positive (price went up)
    # For SELL: profit when net_change is negative (price went down)
    if direction == "BUY":
        profit_loss = net_change * Decimal(str(size))
    else:  # SELL
        profit_loss = -net_change * Decimal(str(size))

    # Calculate profit/loss percentage
    profit_loss_percentage = None
    if open_level != 0:
        if direction == "BUY":
            profit_loss_percentage = (net_change / open_level) * Decimal("100")
        else:  # SELL
            profit_loss_percentage = (-net_change / open_level) * Decimal("100")

    return profit_loss, profit_loss_percentage


async def parse_ig_position_to_schema(
    ig_position_data: PositionData, user: User, db: AsyncSession
) -> Optional[Position]:
    """
    Parse a single IG position data object into our Position schema.

    Args:
        ig_position_data: Typed IG position data from API
        user: User object for database lookups
        db: Database session

    Returns:
        Position object or None if parsing fails
    """
    position_data = ig_position_data.position
    market_data = ig_position_data.market

    if not position_data.deal_id:
        logger.warning("Skipping position without deal ID")
        return None

    # Get market_and_symbol from user's instruments
    market_and_symbol = await get_market_and_symbol_by_ig_epic(
        db, user.id, market_data.epic
    )

    # Extract netChange from market data directly (no need for .get() since it's typed)
    net_change = market_data.net_change

    # Calculate current level and profit/loss using appropriate current price
    # For accurate P&L calculation, we use:
    # - BUY positions: bid price (what you can sell at to close the position)
    # - SELL positions: offer price (what you can buy at to close the position)
    current_level = None
    profit_loss = None
    profit_loss_percentage = None

    # Use bid price for BUY positions (price you can sell at to close)
    # Use offer price for SELL positions (price you can buy at to close)
    if position_data.direction == "BUY" and market_data.bid is not None:
        current_level = market_data.bid
        price_diff = current_level - position_data.level
        profit_loss = price_diff * position_data.size
        if position_data.level != 0:
            profit_loss_percentage = (price_diff / position_data.level) * Decimal("100")
    elif position_data.direction == "SELL" and market_data.offer is not None:
        current_level = market_data.offer
        price_diff = position_data.level - current_level
        profit_loss = price_diff * position_data.size
        if position_data.level != 0:
            profit_loss_percentage = (price_diff / position_data.level) * Decimal("100")
    else:
        # Fallback to net_change method if bid/offer not available
        if net_change is not None and position_data.level:
            current_level = position_data.level + net_change
            profit_loss, profit_loss_percentage = (
                _calculate_profit_loss_from_net_change(
                    position_data.direction,
                    net_change,
                    int(position_data.size),
                    position_data.level,
                )
            )

    # Parse creation date
    created_at = parse_ig_datetime(position_data.created_date_utc)

    # Convert typed values to Decimal where needed
    stop_level = (
        Decimal(str(position_data.stop_level))
        if position_data.stop_level is not None
        else None
    )
    limit_level = (
        Decimal(str(position_data.limit_level))
        if position_data.limit_level is not None
        else None
    )

    return Position(
        deal_id=position_data.deal_id,
        ig_epic=market_data.epic or "",
        market_and_symbol=market_and_symbol,
        direction=position_data.direction,
        size=Decimal(str(position_data.size)),
        open_level=position_data.level,
        current_level=current_level,
        profit_loss=profit_loss,
        profit_loss_percentage=profit_loss_percentage,
        created_at=created_at,
        stop_level=stop_level,
        limit_level=limit_level,
        controlled_risk=position_data.controlled_risk,
    )


async def parse_ig_positions_to_schema(
    ig_positions_data: List[PositionData], user: User, db: AsyncSession
) -> List[Position]:
    """
    Parse a list of IG positions data into our Position schema.

    Args:
        ig_positions_data: List of typed IG position data from API
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

    positions.sort(key=lambda x: x.created_at, reverse=True)
    return positions
