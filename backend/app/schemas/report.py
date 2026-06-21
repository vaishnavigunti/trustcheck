"""Report schemas."""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.report import ReportStatus


class ReportCreateRequest(BaseModel):
    """Request to create a report."""

    verification_id: UUID
    title: Optional[str] = Field(None, max_length=255)

    model_config = ConfigDict(str_strip_whitespace=True)


class ReportResponse(BaseModel):
    """Report response."""

    id: UUID
    verification_id: UUID
    user_id: UUID
    title: str
    file_path: str
    file_size_bytes: int
    status: ReportStatus
    generated_at: datetime
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReportListResponse(BaseModel):
    """List of reports."""

    items: List[ReportResponse]
    total: int


class SharedReportCreateRequest(BaseModel):
    """Request to create a shared report link."""

    report_id: UUID
    # Bounded so a share link cannot be made effectively permanent (or negative).
    expires_days: int = Field(default=30, ge=1, le=90)


class SharedReportResponse(BaseModel):
    """Shared report link response."""

    id: UUID
    report_id: UUID
    token: str
    expires_at: datetime
    share_url: str
    accessed_count: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
