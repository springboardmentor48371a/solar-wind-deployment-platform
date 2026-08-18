import uuid

from pydantic import BaseModel, EmailStr, Field


class UserRegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr = Field(..., max_length=150)
    password: str = Field(..., min_length=8, max_length=72)
    role: str = Field(..., min_length=1, max_length=50)
    phone_number: str | None = Field(default=None, max_length=20)
    organization: str | None = Field(default=None, max_length=150)


class UserRegisterResponse(BaseModel):
    user_id: uuid.UUID
    full_name: str
    email: EmailStr
    role: str
    account_status: str


class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=72)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    user_id: uuid.UUID
    full_name: str
    email: EmailStr
    role: str
    account_status: str
