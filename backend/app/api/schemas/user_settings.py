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
    demo_webhook_secret: Optional[str] = Field(None, description="Demo webhook URL")
    demo_account_id: Optional[str] = Field(
        None, description="Demo spreadbet account ID"
    )
    live_api_key: Optional[str] = Field(None, description="Live API key")
    live_username: Optional[str] = Field(None, description="Live username")
    live_password: Optional[str] = Field(None, description="Live password")
    live_webhook_secret: Optional[str] = Field(None, description="Live webhook URL")
    live_account_id: Optional[str] = Field(
        None, description="Live spreadbet account ID"
    )
    order_type: str = Field(..., description="Order type (e.g., market, limit, stop)")
    maximum_order_age_in_minutes: int = Field(
        ..., description="Maximum age of an order in minutes"
    )
    maximum_open_positions: int = Field(
        ..., description="Maximum number of open positions"
    )
    maximum_open_positions_and_pending_orders: int = Field(
        ..., description="Maximum open positions and pending orders"
    )
    maximum_alert_age_in_seconds: int = Field(
        ..., description="Maximum age of an alert in seconds"
    )
    avoid_dividend_dates: bool = Field(
        ..., description="Avoid trading on dividend dates"
    )
    enforce_maximum_open_positions: bool = Field(
        ..., description="Enforce maximum open positions"
    )
    enforce_maximum_open_positions_and_pending_orders: bool = Field(
        ..., description="Enforce maximum open positions and pending orders"
    )
    enforce_maximum_alert_age_in_seconds: bool = Field(
        ..., description="Enforce maximum alert age in seconds"
    )
    prevent_duplicate_positions_for_instrument: bool = Field(
        ..., description="Prevent duplicate positions for the same instrument"
    )

    class Config:
        from_attributes = True
        use_enum_values = True


class UserSettingsUpdate(BaseModel):
    """Schema for updating user settings"""

    mode: Optional[UserSettingsMode] = Field(
        None, description="Settings mode (demo or live)"
    )
    demo_api_key: Optional[str] = Field(None, description="Demo API key")
    demo_username: Optional[str] = Field(None, description="Demo username")
    demo_password: Optional[str] = Field(None, description="Demo password")
    demo_webhook_secret: Optional[str] = Field(None, description="Demo webhook URL")
    demo_account_id: Optional[str] = Field(
        None, description="Demo spreadbet account ID"
    )
    live_api_key: Optional[str] = Field(None, description="Live API key")
    live_username: Optional[str] = Field(None, description="Live username")
    live_password: Optional[str] = Field(None, description="Live password")
    live_webhook_secret: Optional[str] = Field(None, description="Live webhook URL")
    live_account_id: Optional[str] = Field(
        None, description="Live spreadbet account ID"
    )
    order_type: str = Field(None, description="Order type (e.g., market, limit, stop)")
    maximum_order_age_in_minutes: Optional[int] = Field(
        None, description="Maximum age of an order in minutes"
    )
    maximum_open_positions: Optional[int] = Field(
        None, description="Maximum number of open positions"
    )
    maximum_open_positions_and_pending_orders: Optional[int] = Field(
        None, description="Maximum open positions and pending orders"
    )
    maximum_alert_age_in_seconds: Optional[int] = Field(
        None, description="Maximum age of an alert in seconds"
    )
    avoid_dividend_dates: Optional[bool] = Field(
        None, description="Avoid trading on dividend dates"
    )
    enforce_maximum_open_positions: Optional[bool] = Field(
        None, description="Enforce maximum open positions"
    )
    enforce_maximum_open_positions_and_pending_orders: Optional[bool] = Field(
        None, description="Enforce maximum open positions and pending orders"
    )
    enforce_maximum_alert_age_in_seconds: Optional[bool] = Field(
        None, description="Enforce maximum alert age in seconds"
    )
    prevent_duplicate_positions_for_instrument: Optional[bool] = Field(
        None, description="Prevent duplicate positions for the same instrument"
    )

    class Config:
        from_attributes = True
        use_enum_values = True
