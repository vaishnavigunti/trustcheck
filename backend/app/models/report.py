"""Report model for generated PDF reports."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.shared_report import SharedReport
    from app.models.user import User
    from app.models.verification import Verification


class ReportStatus(str, enum.Enum):
    """Report status enum."""

    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class Report(Base):
    """Generated verification report."""

    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    verification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("verifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(255),
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
    status: Mapped[ReportStatus] = mapped_column(
        Enum(ReportStatus),
        default=ReportStatus.GENERATING,
        nullable=False,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    verification: Mapped["Verification"] = relationship(
        "Verification",
        back_populates="reports",
    )
    user: Mapped["User"] = relationship("User", back_populates="reports")
    shared_links: Mapped[List["SharedReport"]] = relationship(
        "SharedReport",
        back_populates="report",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def is_accessible(self) -> bool:
        """Check if report file is accessible."""
        return self.status == ReportStatus.COMPLETED

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, status={self.status}, verification_id={self.verification_id})>"
