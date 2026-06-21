"""User repository."""

from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for user operations."""

    def __init__(self):
        super().__init__(User)

    async def get_by_email(
        self,
        db: AsyncSession,
        email: str,
    ) -> Optional[User]:
        """Get user by email."""
        result = await db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_relations(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> Optional[User]:
        """Get user by ID with all relationships loaded."""
        from sqlalchemy.orm import selectinload

        result = await db.execute(
            select(User)
            .options(
                selectinload(User.refresh_tokens),
                selectinload(User.verifications),
            )
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def email_exists(
        self,
        db: AsyncSession,
        email: str,
    ) -> bool:
        """Check if email already exists."""
        result = await db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none() is not None

    async def create_user(
        self,
        db: AsyncSession,
        *,
        email: str,
        hashed_password: str,
        full_name: str,
    ) -> User:
        """Create a new user."""
        user = User(
            email=email.lower(),
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
            email_verified=False,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user

    async def update_last_login(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> None:
        """Update user's last login timestamp."""
        from datetime import datetime

        user = await self.get_by_id(db, user_id)
        if user:
            user.last_login_at = datetime.utcnow()
            await db.flush()


# Singleton instance
user_repository = UserRepository()
