"""Verification schemas."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from app.models.verification import VerificationStatus, VerificationType
from app.models.verification_finding import FindingCategory, FindingSeverity


class VerificationCreateRequest(BaseModel):
    """Request to create a new verification."""

    verification_type: VerificationType
    target_url: Optional[str] = Field(None, max_length=2048)
    recruiter_email: Optional[str] = Field(None, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)

    model_config = ConfigDict(str_strip_whitespace=True)


class VerificationResponse(BaseModel):
    """Verification response."""

    id: UUID
    user_id: UUID
    verification_type: VerificationType
    target_url: Optional[str]
    recruiter_email: Optional[str]
    company_name: Optional[str]
    status: VerificationStatus
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    processing_time_ms: Optional[int]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VerificationDetailResponse(VerificationResponse):
    """Detailed verification response with findings."""

    # The ORM relationship is named `evidence_timeline`; read from it but keep
    # the JSON key `timeline` (what the frontend consumes).
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    findings: List["VerificationFindingResponse"] = []
    timeline: List["EvidenceTimelineResponse"] = Field(
        default=[], validation_alias="evidence_timeline"
    )
    pdf_extracted_data: Optional["PDFExtractedDataResponse"] = None


class VerificationFindingResponse(BaseModel):
    """Verification finding response."""

    id: UUID
    category: FindingCategory
    check_name: str
    severity: FindingSeverity
    title: str
    description: Optional[str]
    evidence: Dict[str, Any]
    recommendation: Optional[str]
    sequence_order: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EvidenceTimelineResponse(BaseModel):
    """Evidence timeline entry response."""

    id: UUID
    event_type: str
    sequence_order: int
    timestamp: datetime
    title: str
    description: Optional[str]
    data: Dict[str, Any]
    duration_ms: Optional[int]

    model_config = ConfigDict(from_attributes=True)


class PDFExtractedDataResponse(BaseModel):
    """PDF extracted data response."""

    id: UUID
    extracted_company_name: Optional[str]
    extracted_email: Optional[str]
    extracted_website: Optional[str]
    extracted_address: Optional[str]
    extracted_phone: Optional[str]
    extracted_position: Optional[str]
    extracted_salary: Optional[str]
    extracted_start_date: Optional[str]
    extraction_errors: List[str]

    model_config = ConfigDict(from_attributes=True)


class VerificationListResponse(BaseModel):
    """List of verifications with pagination."""

    items: List[VerificationResponse]
    total: int
    page: int
    page_size: int


class VerificationSummaryResponse(BaseModel):
    """Summary statistics for verifications."""

    total: int
    completed: int
    pending: int
    failed: int
    this_month: int


class FileUploadResponse(BaseModel):
    """File upload response."""

    file_id: UUID
    filename: str
    file_size_bytes: int
    mime_type: str


class StartVerificationRequest(BaseModel):
    """Request to start verification with optional file."""

    verification_type: VerificationType
    target_url: Optional[str] = Field(None, max_length=2048)
    recruiter_email: Optional[str] = Field(None, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)
    file_id: Optional[UUID] = None  # Optional uploaded file ID


# Update forward references
VerificationDetailResponse.model_rebuild()
