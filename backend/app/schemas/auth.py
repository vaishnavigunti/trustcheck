"""Authentication schemas."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserRegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=255)

    model_config = ConfigDict(str_strip_whitespace=True)


class UserLoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str

    model_config = ConfigDict(str_strip_whitespace=True)


class TokenResponse(BaseModel):
    """Token response for login/register."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenRefreshRequest(BaseModel):
    """Token refresh request.

    refresh_token is optional: when omitted, the endpoint falls back to the
    http-only refresh_token cookie (the normal browser flow).
    """

    refresh_token: Optional[str] = None


class TokenPayload(BaseModel):
    """JWT token payload."""

    sub: str  # user_id
    exp: datetime
    type: str


class PasswordChangeRequest(BaseModel):
    """Password change request."""

    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)


class ProfileUpdateRequest(BaseModel):
    """Profile update request (full_name only for now)."""

    full_name: Optional[str] = Field(None, min_length=2, max_length=255)

    model_config = ConfigDict(str_strip_whitespace=True)


class AuthUserResponse(BaseModel):
    """User info in auth responses."""

    id: UUID
    email: str
    full_name: str
    is_active: bool
    email_verified: bool

    model_config = ConfigDict(from_attributes=True)


class LoginResponse(BaseModel):
    """Complete login response."""

    user: AuthUserResponse
    tokens: TokenResponse


class RegisterResponse(BaseModel):
    """Complete registration response."""

    user: AuthUserResponse
    tokens: TokenResponse
    message: str = "Registration successful"


class LogoutResponse(BaseModel):
    """Logout response."""

    message: str = "Logout successful"


class CurrentUserResponse(BaseModel):
    """Current user info response."""

    id: UUID
    email: str
    full_name: str
    is_active: bool
    email_verified: bool
    last_login_at: Optional[datetime]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
