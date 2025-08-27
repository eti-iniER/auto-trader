from pydantic import BaseModel, Field


class AppSettingsRead(BaseModel):
    """Schema for reading app settings"""

    allow_user_registration: bool = Field(
        ..., description="Whether new user registration is allowed"
    )
    allow_multiple_admins: bool = Field(
        ..., description="Whether multiple admin users are allowed"
    )


class AppSettingsUpdate(BaseModel):
    """Schema for updating app settings"""

    allow_user_registration: bool = Field(
        ..., description="Whether new user registration is allowed"
    )
    allow_multiple_admins: bool = Field(
        ..., description="Whether multiple admin users are allowed"
    )
