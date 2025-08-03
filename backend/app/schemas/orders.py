from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field
from app.schemas.instruments import PaginatedResponse


class Order(BaseModel):
    """Order response model matching the frontend interface."""

    deal_id: str
    ig_epic: str
    direction: str
    type: str
    size: float
    created_at: datetime
    stop_level: Optional[float] = None
    profit_level: Optional[float] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# Type alias for paginated orders response
PaginatedOrdersResponse = PaginatedResponse[Order]
