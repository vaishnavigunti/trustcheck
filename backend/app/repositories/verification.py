"""Verification repository."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.verification import Verification
from app.repositories.base import BaseRepository


class VerificationRepository(BaseRepository[Verification]):
    """Repository for verification operations."""

    def __init__(self):
        super().__init__(Verification)

    async def get_by_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        skip: int = 0,
        limit: int = 20,
    ) -> List[Verification]:
        """Get verifications by user with pagination."""
        result = await db.execute(
            select(Verification)
            .where(Verification.user_id == user_id)
            .order_by(desc(Verification.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id_with_details(
        self,
        db: AsyncSession,
        verification_id: UUID,
    ) -> Optional[Verification]:
        """Get verification by ID with all details loaded."""
        from sqlalchemy.orm import selectinload

        result = await db.execute(
            select(Verification)
            .options(
                selectinload(Verification.findings),
                selectinload(Verification.evidence_timeline),
                selectinload(Verification.pdf_extracted_data),
            )
            .where(Verification.id == verification_id)
        )
        return result.scalar_one_or_none()

    async def count_by_user(
        self,
        db: AsyncSession,
        user_id: UUID,
    ) -> int:
        """Count total verifications for a user."""
        from sqlalchemy import func

        result = await db.execute(
            select(func.count())
            .select_from(Verification)
            .where(Verification.user_id == user_id)
        )
        return result.scalar_one()

    async def get_recent_by_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        limit: int = 5,
    ) -> List[Verification]:
        """Get recent verifications for a user."""
        result = await db.execute(
            select(Verification)
            .where(Verification.user_id == user_id)
            .order_by(desc(Verification.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())


# Singleton instance
verification_repository = VerificationRepository()
