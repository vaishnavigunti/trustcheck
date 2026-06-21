"""PDF extracted data model."""

import uuid
from typing import TYPE_CHECKING, Dict, List, Optional

from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.verification import Verification


class PDFExtractedData(Base):
    """Data extracted from uploaded PDF offer letters."""

    __tablename__ = "pdf_extracted_data"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    verification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("verifications.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    raw_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    extracted_company_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    extracted_email: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    extracted_website: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
    )
    extracted_address: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )
    extracted_phone: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )
    extracted_position: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
    )
    extracted_salary: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    extracted_start_date: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )
    other_entities: Mapped[Optional[Dict]] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    extraction_confidence: Mapped[Optional[float]] = mapped_column(
        nullable=True,
    )
    extraction_errors: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )

    # Relationships
    verification: Mapped["Verification"] = relationship(
        "Verification",
        back_populates="pdf_extracted_data",
    )

    def __repr__(self) -> str:
        return f"<PDFExtractedData(id={self.id}, verification_id={self.verification_id})>"
