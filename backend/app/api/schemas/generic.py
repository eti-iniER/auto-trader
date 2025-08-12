from typing import Dict, Optional

from pydantic import BaseModel, Field


class SimpleResponseSchema(BaseModel):
    message: str = Field(..., description="Response message")


class ErrorResponseSchema(BaseModel):
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, str]] = Field(
        None, description="Optional details about the error"
    )
    code: Optional[str] = Field(
        None, description="Optional error code for programmatic handling"
    )
