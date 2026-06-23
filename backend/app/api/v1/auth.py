"""Authentication API routes."""

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_client_ip,
    get_current_user,
    get_db,
    get_user_agent,
)
from app.core.database import get_db as get_db_session
from app.models.user import User
from app.schemas.auth import (
    CurrentUserResponse,
    LoginResponse,
    LogoutResponse,
    PasswordChangeRequest,
    ProfileUpdateRequest,
    RegisterResponse,
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.core import get_settings
from app.services.auth_service import auth_service

router = APIRouter()


def set_auth_cookies(
    response: Response,
    tokens: TokenResponse,
) -> None:
    """Set authentication cookies."""
    settings = get_settings()
    is_production = settings.is_production
    session_max_age = settings.refresh_token_expire_days * 24 * 60 * 60

    # Access token cookie. Kept readable by the client (not http-only) and given
    # the full session lifetime so it acts as a "session present" marker for the
    # Next.js middleware/route guard. The actual access JWT inside still expires
    # after access_token_expire_minutes; the client silently refreshes it.
    response.set_cookie(
        key="access_token",
        value=tokens.access_token,
        httponly=False,
        secure=is_production,  # True in production (HTTPS), False for local dev (HTTP)
        samesite="lax",
        max_age=session_max_age,
    )

    # Refresh token cookie (http-only, only sent to the refresh endpoint)
    response.set_cookie(
        key="refresh_token",
        value=tokens.refresh_token,
        httponly=True,
        secure=is_production,
        samesite="lax",
        max_age=session_max_age,
        path="/api/v1/auth/refresh",  # Only sent to refresh endpoint
    )


def clear_auth_cookies(response: Response) -> None:
    """Clear authentication cookies."""
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token", path="/api/v1/auth/refresh")


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
)
async def register(
    request: Request,
    response: Response,
    data: UserRegisterRequest,
    db: AsyncSession = Depends(get_db_session),
) -> RegisterResponse:
    """Register a new user account."""
    result = await auth_service.register(db, data)

    # Set cookies
    set_auth_cookies(response, result.tokens)

    return result


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User login",
)
async def login(
    request: Request,
    response: Response,
    data: UserLoginRequest,
    db: AsyncSession = Depends(get_db_session),
    ip_address: str = Depends(get_client_ip),
    user_agent: str = Depends(get_user_agent),
) -> LoginResponse:
    """Authenticate user and return tokens."""
    result = await auth_service.login(
        db,
        data,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    # Set cookies
    set_auth_cookies(response, result.tokens)

    return result


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="User logout",
)
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    ip_address: str = Depends(get_client_ip),
) -> LogoutResponse:
    """Logout user and revoke refresh token."""
    # Get refresh token from cookie
    refresh_token = request.cookies.get("refresh_token")

    if refresh_token:
        await auth_service.logout(
            db,
            refresh_token,
            current_user.id,
            ip_address=ip_address,
        )

    # Clear cookies
    clear_auth_cookies(response)

    return LogoutResponse()


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
)
async def refresh_token(
    request: Request,
    response: Response,
    data: TokenRefreshRequest,
    db: AsyncSession = Depends(get_db_session),
    ip_address: str = Depends(get_client_ip),
) -> TokenResponse:
    """Refresh access token using refresh token."""
    # Use token from body or cookie
    refresh_token_str = data.refresh_token or request.cookies.get("refresh_token")

    if not refresh_token_str:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token required",
        )

    new_tokens = await auth_service.refresh_tokens(
        db,
        refresh_token_str,
        ip_address=ip_address,
    )

    # Update cookies
    set_auth_cookies(response, new_tokens)

    return new_tokens


@router.get(
    "/me",
    response_model=CurrentUserResponse,
    summary="Get current user",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> CurrentUserResponse:
    """Get current authenticated user info."""
    return CurrentUserResponse.model_validate(current_user)


@router.patch(
    "/me",
    summary="Update current user profile",
)
async def update_me(
    data: ProfileUpdateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Update the current user's profile (full_name only for now)."""
    full_name = (data.full_name or "").strip()
    if full_name:
        current_user.full_name = full_name
        db.add(current_user)
        await db.commit()
        await db.refresh(current_user)
    return CurrentUserResponse.model_validate(current_user).model_dump()


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change password",
)
async def change_password(
    request: Request,
    data: PasswordChangeRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    response: Response = None,
) -> dict:
    """Change user password (requires current password)."""
    await auth_service.change_password(
        db,
        current_user.id,
        data.current_password,
        data.new_password,
    )

    # Clear cookies after password change (force re-login)
    if response:
        clear_auth_cookies(response)

    return {"message": "Password changed successfully. Please log in again."}
