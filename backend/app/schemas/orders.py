from datetime import datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel


class Order(BaseModel):
    """Order response model matching the frontend interface."""

    deal_id: str
    ig_epic: str
    direction: str
    type: str
    size: float
    created_at: datetime
    stop_level: Optional[Decimal] = None
    profit_level: Optional[Decimal] = None

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}
