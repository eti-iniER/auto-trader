from datetime import datetime
from typing import Optional
from uuid import UUID

from app.db.enums import LogType
from pydantic import BaseModel


class LogRead(BaseModel):
    """Schema for reading log entries."""

    id: UUID
    message: str
    description: Optional[str] = None
    type: LogType
    extra: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class LogFilters(BaseModel):
    """Schema for log filtering parameters."""

    from_date: Optional[datetime] = None
    to_date: Optional[datetime] = None
    type: Optional[LogType] = None
