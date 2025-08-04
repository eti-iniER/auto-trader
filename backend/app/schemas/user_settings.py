import uuid
from typing import Optional

from app.db.enums import UserSettingsMode
from pydantic import BaseModel, Field


class UserSettingsRead(BaseModel):
    """Schema for reading user settings"""

    mode: UserSettingsMode = Field(
        ..., description="Current settings mode (demo or live)"
    )
    demo_api_key: Optional[str] = Field(None, description="Demo API key")
    demo_username: Optional[str] = Field(None, description="Demo username")
    demo_password: Optional[str] = Field(None, description="Demo password")
    demo_webhook_url: Optional[str] = Field(None, description="Demo webhook URL")
    live_api_key: Optional[str] = Field(None, description="Live API key")
    live_username: Optional[str] = Field(None, description="Live username")
    live_password: Optional[str] = Field(None, description="Live password")
    live_webhook_url: Optional[str] = Field(None, description="Live webhook URL")

    class Config:
        from_attributes = True


class UserSettingsUpdate(BaseModel):
    """Schema for updating user settings"""

    mode: Optional[UserSettingsMode] = Field(
        None, description="Settings mode (demo or live)"
    )
    demo_api_key: Optional[str] = Field(None, description="Demo API key")
    demo_username: Optional[str] = Field(None, description="Demo username")
    demo_password: Optional[str] = Field(None, description="Demo password")
    demo_webhook_url: Optional[str] = Field(None, description="Demo webhook URL")
    live_api_key: Optional[str] = Field(None, description="Live API key")
    live_username: Optional[str] = Field(None, description="Live username")
    live_password: Optional[str] = Field(None, description="Live password")
    live_webhook_url: Optional[str] = Field(None, description="Live webhook URL")
