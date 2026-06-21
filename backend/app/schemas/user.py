"""User schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for creating a user."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=255)

    model_config = ConfigDict(str_strip_whitespace=True)


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None

    model_config = ConfigDict(str_strip_whitespace=True)


class UserInDB(BaseModel):
    """User as stored in database."""

    id: UUID
    email: str
    full_name: str
    is_active: bool
    email_verified: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    hashed_password: str

    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseModel):
    """User response for API."""

    id: UUID
    email: str
    full_name: str
    is_active: bool
    email_verified: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    """Profile update request."""

    full_name: Optional[str] = Field(None, min_length=2, max_length=255)

    model_config = ConfigDict(str_strip_whitespace=True)
