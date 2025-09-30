import uuid
from app.db.enums import UserSettingsMode
from pydantic import AwareDatetime, BaseModel, EmailStr, Field


class UserSchema(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    role: str = Field(..., description="User's role (e.g., USER, ADMIN)")


class UserAdminSchema(UserSchema):
    id: uuid.UUID = Field(..., description="User's unique identifier")
    created_at: AwareDatetime = Field(
        ..., description="Timestamp when the user was created"
    )
    last_login: AwareDatetime = Field(
        ..., description="Timestamp of the user's last login"
    )
    mode: UserSettingsMode = Field(..., description="User's mode (e.g., DEMO, LIVE)")

    model_config = {
        "from_attributes": True,
        "use_enum_values": True,
    }


class UserSettingsModeSchema(BaseModel):
    mode: UserSettingsMode = Field(..., description="User's mode (e.g., DEMO, LIVE)")

    model_config = {
        "from_attributes": True,
        "use_enum_values": True,
    }


class UserUpdateSchema(BaseModel):
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    email: EmailStr = Field(..., description="User's email address")
    role: str = Field(..., description="User's role (e.g., USER, ADMIN)")
