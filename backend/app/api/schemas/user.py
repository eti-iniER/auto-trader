from pydantic import BaseModel, EmailStr, Field


class UserSchema(BaseModel):
    email: EmailStr = Field(..., description="User's email address")
    first_name: str = Field(..., description="User's first name")
    last_name: str = Field(..., description="User's last name")
    role: str = Field(..., description="User's role (e.g., USER, ADMIN)")

    class Config:
        use_enum_values = True
