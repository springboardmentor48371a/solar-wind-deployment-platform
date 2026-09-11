from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

class UserRegister(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100, example="Jane Doe")
    email: EmailStr = Field(..., example="jane.doe@renewable-ai.com")
    password: str = Field(..., min_length=6, max_length=100, example="SecretPassword123")
    role: Optional[str] = Field("gis_analyst", example="gis_analyst")
    confirm_password: Optional[str] = Field(None, example="SecretPassword123")

    @field_validator("confirm_password")
    def passwords_match(cls, v, info):
        if v is not None and "password" in info.data and v != info.data["password"]:
            raise ValueError("Passwords do not match")
        return v

class UserLogin(BaseModel):
    email: EmailStr = Field(..., example="jane.doe@renewable-ai.com")
    password: str = Field(..., example="SecretPassword123")

class UserResponse(BaseModel):
    id: UUID
    full_name: str
    email: EmailStr
    role: str = "gis_analyst"
    created_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class TokenData(BaseModel):
    user_id: Optional[str] = None
