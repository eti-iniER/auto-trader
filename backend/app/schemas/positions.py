from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional
from pydantic import BaseModel, AwareDatetime

# Position direction can be BUY or SELL
type PositionDirection = Literal["BUY", "SELL"]


class Position(BaseModel):
    """Position response model containing the most important data for table display."""

    deal_id: str
    ig_epic: str
    market_and_symbol: Optional[str] = None
    direction: PositionDirection
    size: int
    open_level: Decimal
    current_level: Optional[Decimal] = None
    profit_loss: Optional[Decimal] = None
    profit_loss_percentage: Optional[Decimal] = None
    created_at: AwareDatetime
    stop_level: Optional[Decimal] = None
    limit_level: Optional[Decimal] = None
    controlled_risk: bool = False
