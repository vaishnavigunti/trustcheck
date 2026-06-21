"""Shared report model for public shareable URLs."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.report import Report


class SharedReport(Base):
    """Public shareable report link with signed token."""

    __tablename__ = "shared_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    token: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    accessed_count: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )
    last_accessed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_by_ip: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    report: Mapped["Report"] = relationship("Report", back_populates="shared_links")

    @property
    def is_expired(self) -> bool:
        """Check if share link is expired."""
        return datetime.utcnow() > self.expires_at

    @property
    def is_revoked(self) -> bool:
        """Check if share link is revoked."""
        return self.revoked_at is not None

    @property
    def is_active(self) -> bool:
        """Check if share link is active (not expired and not revoked)."""
        return not self.is_expired and not self.is_revoked

    def record_access(self, ip_address: Optional[str] = None) -> None:
        """Record an access to this shared report."""
        self.accessed_count += 1
        self.last_accessed_at = datetime.utcnow()

    def __repr__(self) -> str:
        return f"<SharedReport(id={self.id}, report_id={self.report_id}, active={self.is_active})>"
