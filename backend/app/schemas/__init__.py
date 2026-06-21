"""Pydantic schemas for API validation and serialization."""

from app.schemas.auth import (
    AuthUserResponse,
    CurrentUserResponse,
    LoginResponse,
    LogoutResponse,
    PasswordChangeRequest,
    RegisterResponse,
    TokenPayload,
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.schemas.user import (
    UserCreate,
    UserInDB,
    UserProfileUpdate,
    UserResponse,
    UserUpdate,
)
from app.schemas.report import (
    ReportCreateRequest,
    ReportListResponse,
    ReportResponse,
    SharedReportCreateRequest,
    SharedReportResponse,
)
from app.schemas.verification import (
    EvidenceTimelineResponse,
    FileUploadResponse,
    PDFExtractedDataResponse,
    StartVerificationRequest,
    VerificationCreateRequest,
    VerificationDetailResponse,
    VerificationFindingResponse,
    VerificationListResponse,
    VerificationResponse,
    VerificationSummaryResponse,
)

__all__ = [
    # Auth schemas
    "UserRegisterRequest",
    "UserLoginRequest",
    "TokenResponse",
    "TokenRefreshRequest",
    "TokenPayload",
    "PasswordChangeRequest",
    "AuthUserResponse",
    "LoginResponse",
    "RegisterResponse",
    "LogoutResponse",
    "CurrentUserResponse",
    # User schemas
    "UserCreate",
    "UserUpdate",
    "UserInDB",
    "UserResponse",
    "UserProfileUpdate",
    # Verification schemas
    "VerificationCreateRequest",
    "VerificationResponse",
    "VerificationDetailResponse",
    "VerificationFindingResponse",
    "EvidenceTimelineResponse",
    "PDFExtractedDataResponse",
    "VerificationListResponse",
    "VerificationSummaryResponse",
    "FileUploadResponse",
    "StartVerificationRequest",
    # Report schemas
    "ReportCreateRequest",
    "ReportResponse",
    "ReportListResponse",
    "SharedReportCreateRequest",
    "SharedReportResponse",
]
