"""Authentication service."""

import hashlib
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_logger, get_password_hash, get_settings, verify_password
from app.core.exceptions import AuthenticationError, ValidationError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    create_public_report_token,
    verify_token,
)
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories import user_repository
from app.schemas.auth import (
    LoginResponse,
    RegisterResponse,
    TokenPayload,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)

logger = get_logger(__name__)


class AuthService:
    """Authentication service layer."""

    def __init__(self):
        self.settings = get_settings()

    async def register(
        self,
        db: AsyncSession,
        data: UserRegisterRequest,
    ) -> RegisterResponse:
        """Register a new user."""
        # Check if email exists
        if await user_repository.email_exists(db, data.email):
            raise ValidationError("Email already registered")

        # Create user
        hashed_password = get_password_hash(data.password)
        user = await user_repository.create_user(
            db=db,
            email=data.email,
            hashed_password=hashed_password,
            full_name=data.full_name,
        )

        # Generate tokens
        tokens = self._generate_tokens(str(user.id))

        # Persist refresh token hash so the new user can refresh immediately
        # (without this, /auth/refresh rejects the token until first login).
        await self._store_refresh_token(db, user.id, tokens.refresh_token)

        logger.info("User registered", user_id=str(user.id), email=user.email)

        from app.schemas.auth import AuthUserResponse

        return RegisterResponse(
            user=AuthUserResponse.model_validate(user),
            tokens=tokens,
        )

    async def login(
        self,
        db: AsyncSession,
        data: UserLoginRequest,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> LoginResponse:
        """Authenticate user and return tokens."""
        # Find user
        user = await user_repository.get_by_email(db, data.email)
        if not user:
            # Log failed attempts so brute-force / credential-stuffing is
            # visible in monitoring. Never log the password itself.
            logger.warning(
                "Failed login: unknown email",
                email=data.email,
                ip_address=ip_address,
            )
            raise AuthenticationError("Invalid credentials")

        # Check if active
        if not user.is_active:
            logger.warning(
                "Failed login: disabled account",
                user_id=str(user.id),
                ip_address=ip_address,
            )
            raise AuthenticationError("Account is disabled")

        # Verify password
        if not verify_password(data.password, user.hashed_password):
            logger.warning(
                "Failed login: bad password",
                user_id=str(user.id),
                ip_address=ip_address,
            )
            raise AuthenticationError("Invalid credentials")

        # Update last login
        await user_repository.update_last_login(db, user.id)

        # Generate tokens
        tokens = self._generate_tokens(str(user.id))

        # Store refresh token hash
        await self._store_refresh_token(db, user.id, tokens.refresh_token)

        logger.info(
            "User logged in",
            user_id=str(user.id),
            ip_address=ip_address,
        )

        from app.schemas.auth import AuthUserResponse

        return LoginResponse(
            user=AuthUserResponse.model_validate(user),
            tokens=tokens,
        )

    async def logout(
        self,
        db: AsyncSession,
        refresh_token: str,
        user_id: UUID,
        ip_address: Optional[str] = None,
    ) -> None:
        """Logout user by revoking refresh token."""
        # Hash the token to find it
        token_hash = self._hash_token(refresh_token)

        # Find and revoke token
        from sqlalchemy import select

        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.user_id == user_id,
            )
        )
        token = result.scalar_one_or_none()

        if token:
            token.revoked_at = datetime.utcnow()
            token.revoked_by_ip = ip_address
            await db.flush()

        logger.info("User logged out", user_id=str(user_id))

    async def refresh_tokens(
        self,
        db: AsyncSession,
        refresh_token: str,
        ip_address: Optional[str] = None,
    ) -> TokenResponse:
        """Refresh access token using refresh token."""
        # Verify refresh token
        payload = verify_token(refresh_token, expected_type="refresh")
        if not payload:
            raise AuthenticationError("Invalid or expired refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")

        # The JWT "sub" claim is a string; the column is UUID-typed, so coerce
        # before querying (otherwise the SQLAlchemy UUID binder raises).
        try:
            user_uuid = UUID(user_id)
        except (ValueError, TypeError):
            raise AuthenticationError("Invalid token payload")

        # Check if token is revoked
        token_hash = self._hash_token(refresh_token)
        from sqlalchemy import select

        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.user_id == user_uuid,
            )
        )
        stored_token = result.scalar_one_or_none()

        if not stored_token or not stored_token.is_valid:
            raise AuthenticationError("Refresh token is revoked or expired")

        # Revoke old token
        stored_token.revoked_at = datetime.utcnow()
        stored_token.revoked_by_ip = ip_address

        # Generate new tokens
        new_tokens = self._generate_tokens(user_id)

        # Store new refresh token
        await self._store_refresh_token(db, user_uuid, new_tokens.refresh_token)

        logger.info("Tokens refreshed", user_id=user_id)

        return new_tokens

    async def change_password(
        self,
        db: AsyncSession,
        user_id: UUID,
        current_password: str,
        new_password: str,
    ) -> None:
        """Change user password."""
        user = await user_repository.get_by_id(db, user_id)
        if not user:
            raise AuthenticationError("User not found")

        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise AuthenticationError("Current password is incorrect")

        # Update password
        user.hashed_password = get_password_hash(new_password)
        await db.flush()

        # Revoke all refresh tokens
        await self._revoke_all_user_tokens(db, user_id)

        logger.info("Password changed", user_id=str(user_id))

    async def get_current_user(
        self,
        db: AsyncSession,
        token: str,
    ) -> User:
        """Get current user from access token."""
        payload = verify_token(token, expected_type="access")
        if not payload:
            raise AuthenticationError("Invalid or expired token")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid token payload")

        user = await user_repository.get_by_id(db, UUID(user_id))
        if not user:
            raise AuthenticationError("User not found")

        if not user.is_active:
            raise AuthenticationError("Account is disabled")

        return user

    def _generate_tokens(self, user_id: str) -> TokenResponse:
        """Generate access and refresh tokens."""
        token_data = {"sub": user_id}

        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=self.settings.access_token_expire_minutes * 60,
        )

    async def _store_refresh_token(
        self,
        db: AsyncSession,
        user_id: UUID,
        token: str,
    ) -> None:
        """Store refresh token hash in database."""
        token_hash = self._hash_token(token)
        expires_at = datetime.utcnow() + timedelta(
            days=self.settings.refresh_token_expire_days
        )

        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        db.add(refresh_token)
        await db.flush()

    async def _revoke_all_user_tokens(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> None:
        """Revoke all refresh tokens for a user."""
        from sqlalchemy import select

        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == user_id,
                RefreshToken.revoked_at.is_(None),
            )
        )
        tokens = result.scalars().all()

        for token in tokens:
            token.revoked_at = datetime.utcnow()

        await db.flush()

    def _hash_token(self, token: str) -> str:
        """Hash a token for storage."""
        return hashlib.sha256(token.encode()).hexdigest()


# Singleton instance
auth_service = AuthService()
