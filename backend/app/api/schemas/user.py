from pydantic import BaseModel, EmailStr, Field


class UserSchema(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    role: str = Field(..., description="User's role (e.g., USER, ADMIN)")


class UserDetailsSchema(UserSchema):
    id: str = Field(..., description="User's unique identifier")
    created_at: str = Field(..., description="Timestamp when the user was created")
    updated_at: str = Field(..., description="Timestamp when the user was last updated")
    last_login: str = Field(..., description="Timestamp of the user's last login")
