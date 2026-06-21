"""Verification model."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Dict, List, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.evidence_timeline import EvidenceTimeline
    from app.models.pdf_extracted_data import PDFExtractedData
    from app.models.report import Report
    from app.models.uploaded_file import UploadedFile
    from app.models.user import User
    from app.models.verification_finding import VerificationFinding


class VerificationStatus(str, enum.Enum):
    """Verification status enum."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class VerificationType(str, enum.Enum):
    """Verification type enum."""

    COMPANY = "company"
    RECRUITER = "recruiter"
    OFFER_LETTER = "offer_letter"
    WEBSITE = "website"


class Verification(Base):
    """Verification job model."""

    __tablename__ = "verifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    verification_type: Mapped[VerificationType] = mapped_column(
        Enum(VerificationType),
        nullable=False,
    )
    target_url: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
    )
    recruiter_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )
    company_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus),
        default=VerificationStatus.PENDING,
        nullable=False,
        index=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    processing_time_ms: Mapped[Optional[int]] = mapped_column(
        nullable=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    verification_metadata: Mapped[Optional[Dict]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="verifications")
    findings: Mapped[List["VerificationFinding"]] = relationship(
        "VerificationFinding",
        back_populates="verification",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="VerificationFinding.created_at",
    )
    evidence_timeline: Mapped[List["EvidenceTimeline"]] = relationship(
        "EvidenceTimeline",
        back_populates="verification",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="EvidenceTimeline.sequence_order",
    )
    uploaded_files: Mapped[List["UploadedFile"]] = relationship(
        "UploadedFile",
        back_populates="verification",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    pdf_extracted_data: Mapped[Optional["PDFExtractedData"]] = relationship(
        "PDFExtractedData",
        back_populates="verification",
        cascade="all, delete-orphan",
        uselist=False,
        lazy="selectin",
    )
    reports: Mapped[List["Report"]] = relationship(
        "Report",
        back_populates="verification",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate duration in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def __repr__(self) -> str:
        return f"<Verification(id={self.id}, type={self.verification_type}, status={self.status})>"
