"""
Helpers for parsing IG orders data into our Order schema.
"""

import logging
from typing import List, Optional

from app.api.helpers.ig_utils import parse_ig_datetime
from app.api.schemas.orders import Order

logger = logging.getLogger(__name__)


def _calculate_stop_and_profit_levels(
    direction: str,
    order_level: float,
    stop_distance: Optional[float],
    limit_distance: Optional[float],
) -> tuple[Optional[float], Optional[float]]:
    """
    Calculate stop and profit levels based on direction and distances.

    Args:
        direction: Order direction (BUY or SELL)
        order_level: Order execution level
        stop_distance: Stop distance from order level
        limit_distance: Limit distance from order level

    Returns:
        Tuple of (stop_level, profit_level)
    """
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
        else:  # SELL
            profit_level = order_level - limit_distance

    return stop_level, profit_level


def parse_ig_order_to_schema(ig_order_data: dict) -> Optional[Order]:
    """
    Parse a single IG order data object into our Order schema.

    Args:
        ig_order_data: Raw order data from IG API

    Returns:
        Order object or None if parsing fails
    """
    working_order_data = ig_order_data.get("workingOrderData", {})
    market_data = ig_order_data.get("marketData", {})

    deal_id = working_order_data.get("dealId", "")
    if not deal_id:
        logger.warning("Skipping order without deal ID")
        return None

    ig_epic = working_order_data.get("epic", market_data.get("epic", ""))
    direction = working_order_data.get("direction", "").upper()
    order_type = working_order_data.get("orderType", "")
    size = working_order_data.get("orderSize", 0)

    # Parse creation date
    created_at = parse_ig_datetime(working_order_data.get("createdDateUTC"))

    # Calculate stop and profit levels
    order_level = working_order_data.get("orderLevel", 0.0)
    stop_distance = working_order_data.get("stopDistance")
    limit_distance = working_order_data.get("limitDistance")

    stop_level, profit_level = _calculate_stop_and_profit_levels(
        direction, order_level, stop_distance, limit_distance
    )

    return Order(
        deal_id=deal_id,
        ig_epic=ig_epic,
        direction=direction,
        type=order_type,
        size=size,
        entry_level=order_level,
        created_at=created_at,
        stop_level=stop_level,
        profit_level=profit_level,
    )


def parse_ig_orders_to_schema(ig_orders_data: List[dict]) -> List[Order]:
    """
    Parse a list of IG orders data into our Order schema.

    Args:
        ig_orders_data: List of raw order data from IG API

    Returns:
        List of Order objects, sorted by creation date (most recent first)
    """
    orders = []

    for ig_order_data in ig_orders_data:
        order = parse_ig_order_to_schema(ig_order_data)
        if order:
            orders.append(order)

    # Sort by creation date, most recent first
    orders.sort(key=lambda x: x.created_at, reverse=True)
    return orders
