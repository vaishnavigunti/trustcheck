"""Verification finding model."""

import enum
import uuid
from typing import TYPE_CHECKING, Dict, Optional

from sqlalchemy import Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.verification import Verification


class FindingCategory(str, enum.Enum):
    """Finding category enum."""

    DOMAIN = "domain"
    SSL = "ssl"
    DNS = "dns"
    EMAIL = "email"
    WEBSITE = "website"
    PDF = "pdf"
    SYSTEM = "system"


class FindingSeverity(str, enum.Enum):
    """Finding severity enum."""

    PASSED = "passed"
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class VerificationFinding(Base):
    """Individual verification finding/check result."""

    __tablename__ = "verification_findings"

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
    category: Mapped[FindingCategory] = mapped_column(
        Enum(FindingCategory),
        nullable=False,
        index=True,
    )
    check_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    severity: Mapped[FindingSeverity] = mapped_column(
        Enum(FindingSeverity),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    evidence: Mapped[Optional[Dict]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    recommendation: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    sequence_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Relationships
    verification: Mapped["Verification"] = relationship(
        "Verification",
        back_populates="findings",
    )

    def __repr__(self) -> str:
        return f"<VerificationFinding(id={self.id}, category={self.category}, severity={self.severity})>"
