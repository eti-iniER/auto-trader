from typing import Optional

from pydantic import AwareDatetime, BaseModel, Field


class WebhookPayload(BaseModel):
    message: str = Field(..., description="The message associated with the webhook")
    secret: str = Field(..., description="Secret key for webhook validation")
    timestamp: AwareDatetime = Field(
        ..., description="The timestamp when the webhook was triggered"
    )
    received_at: Optional[AwareDatetime] = Field(
        None, description="The timestamp when the webhook was received"
    )
