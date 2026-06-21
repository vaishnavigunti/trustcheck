"""Evidence timeline model for chronological findings."""

import enum
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Dict, Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.verification import Verification


class TimelineEventType(str, enum.Enum):
    """Timeline event type enum."""

    VERIFICATION_STARTED = "verification_started"
    DOMAIN_CHECK = "domain_check"
    SSL_CHECK = "ssl_check"
    DNS_CHECK = "dns_check"
    WEBSITE_ANALYSIS = "website_analysis"
    EMAIL_VERIFICATION = "email_verification"
    PDF_EXTRACTION = "pdf_extraction"
    CROSS_VALIDATION = "cross_validation"
    VERIFICATION_COMPLETED = "verification_completed"
    VERIFICATION_FAILED = "verification_failed"


class EvidenceTimeline(Base):
    """Chronological evidence timeline for verifications."""

    __tablename__ = "evidence_timeline"

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
    event_type: Mapped[TimelineEventType] = mapped_column(
        Enum(TimelineEventType),
        nullable=False,
    )
    sequence_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    data: Mapped[Optional[Dict]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    duration_ms: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Relationships
    verification: Mapped["Verification"] = relationship(
        "Verification",
        back_populates="evidence_timeline",
    )

    def __repr__(self) -> str:
        return f"<EvidenceTimeline(id={self.id}, event={self.event_type}, sequence={self.sequence_order})>"
