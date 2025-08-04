from pydantic import BaseModel, Field


class SimpleResponseSchema(BaseModel):
    message: str = Field(..., description="Response message")
