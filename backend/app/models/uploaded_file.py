"""Uploaded file model."""

import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.verification import Verification


class UploadedFile(Base):
    """Uploaded file metadata."""

    __tablename__ = "uploaded_files"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    # Owner of the upload. Recorded at upload time so that linking a file to a
    # verification can enforce ownership (prevents IDOR — attaching someone
    # else's uploaded file by guessing its id). Nullable only for rows created
    # before this column existed.
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    # Nullable: a file is uploaded *before* its verification exists, then linked
    # once the verification is created. A non-null FK here would violate the
    # foreign key constraint on PostgreSQL at upload time.
    verification_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("verifications.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    original_filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    stored_filename: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    file_size_bytes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    mime_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    file_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    # Relationships
    verification: Mapped[Optional["Verification"]] = relationship(
        "Verification",
        back_populates="uploaded_files",
    )

    @property
    def file_size_mb(self) -> float:
        """Convert bytes to MB."""
        return self.file_size_bytes / (1024 * 1024)

    def __repr__(self) -> str:
        return f"<UploadedFile(id={self.id}, filename={self.original_filename})>"
