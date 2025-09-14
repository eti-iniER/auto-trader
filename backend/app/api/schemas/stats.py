from typing import List
from pydantic import BaseModel, AwareDatetime, Field

from app.clients.ig.types import Activity


class UserQuickStatsResponse(BaseModel):
    """Response model for user quick stats endpoint"""

    open_positions_count: int = Field(
        ..., description="Number of currently open positions"
    )
    open_orders_count: int = Field(..., description="Number of open working orders")
    recent_activities: List[Activity] = Field(
        ..., description="Recent account activities from the last day"
    )
    stats_timestamp: AwareDatetime = Field(
        ..., description="Timestamp when these stats were generated"
    )
