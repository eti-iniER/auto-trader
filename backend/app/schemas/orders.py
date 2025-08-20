from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional
from pydantic import BaseModel, AwareDatetime

# Order type can be either MARKET, LIMIT, or STOP
type WorkingOrderType = Literal["LIMIT", "MARKET", "STOP"]


class Order(BaseModel):
    """Order response model matching the frontend interface."""

    deal_id: str
    ig_epic: str
    direction: str
    type: WorkingOrderType
    size: Decimal
    created_at: AwareDatetime
    stop_level: Optional[Decimal] = None
    profit_level: Optional[Decimal] = None
