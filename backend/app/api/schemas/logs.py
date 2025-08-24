from typing import Optional
from uuid import UUID

from app.db.enums import LogType
from pydantic import AwareDatetime, BaseModel


class LogRead(BaseModel):
    """Schema for reading log entries."""

    id: UUID
    message: str
    description: Optional[str] = None
    type: LogType
    extra: Optional[dict] = None
    created_at: AwareDatetime

    class Config:
        from_attributes = True
