"""Base repository with generic CRUD operations."""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base repository with common database operations."""

    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get_by_id(
        self,
        db: AsyncSession,
        id: Union[UUID, str],
    ) -> Optional[ModelType]:
        """Get a record by ID."""
        result = await db.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> List[ModelType]:
        """Get multiple records with pagination."""
        result = await db.execute(
            select(self.model)
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def create(
        self,
        db: AsyncSession,
        *,
        obj_in: Dict[str, Any],
    ) -> ModelType:
        """Create a new record."""
        db_obj = self.model(**obj_in)
        db.add(db_obj)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: Dict[str, Any],
    ) -> ModelType:
        """Update a record."""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        await db.flush()
        await db.refresh(db_obj)
        return db_obj

    async def delete(
        self,
        db: AsyncSession,
        *,
        id: Union[UUID, str],
    ) -> bool:
        """Delete a record by ID."""
        result = await db.execute(
            select(self.model).where(self.model.id == id)
        )
        obj = result.scalar_one_or_none()
        if obj:
            await db.delete(obj)
            await db.flush()
            return True
        return False

    async def count(
        self,
        db: AsyncSession,
    ) -> int:
        """Count all records."""
        from sqlalchemy import func
        result = await db.execute(select(func.count()).select_from(self.model))
        return result.scalar_one()
