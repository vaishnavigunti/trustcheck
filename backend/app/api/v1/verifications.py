"""Verification API routes."""

import hashlib
import shutil
from pathlib import Path
from typing import List, Optional
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_client_ip, get_current_user, get_db
from app.core import get_logger, get_settings
from app.core.rate_limit import generation_limiter, rate_limit
from app.core.database import get_db as get_db_session
from app.core.exceptions import NotFoundError, ValidationError
from app.models.uploaded_file import UploadedFile
from app.models.user import User
from app.models.verification import Verification, VerificationStatus, VerificationType
from app.repositories import verification_repository
from app.schemas.verification import (
    FileUploadResponse,
    StartVerificationRequest,
    VerificationCreateRequest,
    VerificationDetailResponse,
    VerificationListResponse,
    VerificationResponse,
    VerificationSummaryResponse,
)
from app.services.verification_service import run_verification_in_background

logger = get_logger(__name__)
router = APIRouter()


def _get_upload_path() -> Path:
    """Get upload directory path."""
    settings = get_settings()
    upload_path = settings.upload_path
    upload_path.mkdir(parents=True, exist_ok=True)
    return upload_path


def _validate_file(file: UploadFile) -> None:
    """Validate uploaded file metadata (extension + declared content type)."""
    settings = get_settings()

    # Check file extension
    if file.filename:
        ext = Path(file.filename).suffix.lower().lstrip(".")
        if ext not in settings.allowed_extensions:
            raise ValidationError(f"File type .{ext} not allowed. Only PDF files are accepted.")

    # Check content type (client-supplied — verified again via magic bytes below)
    if file.content_type != "application/pdf":
        raise ValidationError("Only PDF files are allowed")


@router.post(
    "/upload",
    response_model=FileUploadResponse,
    summary="Upload PDF file",
)
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> FileUploadResponse:
    """Upload a PDF file for verification."""
    settings = get_settings()

    # Validate file
    _validate_file(file)

    # Check file size
    content = await file.read()
    if len(content) > settings.max_file_size_bytes:
        raise ValidationError(f"File size exceeds maximum of {settings.max_file_size_mb}MB")

    if not content:
        raise ValidationError("Uploaded file is empty")

    # Verify the actual bytes are a PDF — the declared content type / extension
    # are client-controlled and can be spoofed. Every PDF starts with "%PDF-".
    if not content.startswith(b"%PDF-"):
        raise ValidationError("File content is not a valid PDF")

    # Calculate hash
    file_hash = hashlib.sha256(content).hexdigest()

    # Generate unique filename
    stored_filename = f"{uuid4()}.pdf"
    upload_path = _get_upload_path() / "pdfs"
    upload_path.mkdir(parents=True, exist_ok=True)
    file_path = upload_path / stored_filename

    # Save file
    with open(file_path, "wb") as f:
        f.write(content)

    # Create database record (not yet linked to a verification — that happens
    # when the verification is created via the file_id reference). The owner is
    # recorded so linking can enforce ownership later.
    uploaded_file = UploadedFile(
        user_id=current_user.id,
        verification_id=None,
        original_filename=file.filename or "unknown.pdf",
        stored_filename=stored_filename,
        file_path=str(file_path),
        file_size_bytes=len(content),
        mime_type="application/pdf",
        file_hash=file_hash,
    )
    db.add(uploaded_file)
    await db.flush()

    logger.info(
        "File uploaded",
        file_id=str(uploaded_file.id),
        user_id=str(current_user.id),
        filename=file.filename,
    )

    return FileUploadResponse(
        file_id=uploaded_file.id,
        filename=uploaded_file.original_filename,
        file_size_bytes=uploaded_file.file_size_bytes,
        mime_type=uploaded_file.mime_type,
    )


@router.post(
    "/",
    response_model=VerificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and start verification",
    dependencies=[Depends(rate_limit(generation_limiter))],
)
async def create_verification(
    request: Request,
    data: StartVerificationRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> VerificationResponse:
    """Create a verification and run it asynchronously.

    The verification (domain/SSL/DNS/website/PDF checks) can take tens of
    seconds, which would exceed typical gateway timeouts if done inline. We
    persist the record as ``pending`` and run the checks in a background task;
    clients poll ``GET /verifications/{id}`` for the result.
    """

    # Validate at least one target is provided
    if not data.target_url and not data.recruiter_email:
        raise ValidationError("Either target_url or recruiter_email must be provided")

    # SSRF guard: reject URLs that point at internal / non-public addresses
    # before we ever queue an outbound fetch against them.
    if data.target_url:
        from app.core.ssrf import SSRFError, validate_public_url

        normalized = data.target_url.strip()
        if not normalized.lower().startswith(("http://", "https://")):
            normalized = f"https://{normalized}"
        try:
            validate_public_url(normalized)
        except SSRFError as e:
            raise ValidationError(f"Invalid target URL: {e}")

    # Create verification record
    verification = Verification(
        user_id=current_user.id,
        verification_type=data.verification_type,
        target_url=data.target_url,
        recruiter_email=data.recruiter_email,
        company_name=data.company_name,
        status=VerificationStatus.PENDING,
    )
    db.add(verification)
    await db.flush()

    # If file uploaded, link it to this verification
    pdf_path = None
    if data.file_id:
        from sqlalchemy import select
        from app.models.uploaded_file import UploadedFile

        result = await db.execute(
            select(UploadedFile).where(UploadedFile.id == data.file_id)
        )
        uploaded_file = result.scalar_one_or_none()
        # Ownership check: only the user who uploaded the file may attach it.
        if uploaded_file and uploaded_file.user_id not in (None, current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to use this file",
            )
        if uploaded_file:
            uploaded_file.verification_id = verification.id
            pdf_path = uploaded_file.file_path

    # Commit so the record is visible to the background task's own session.
    await db.commit()
    await db.refresh(verification)

    # Run the verification after the response is sent.
    background_tasks.add_task(
        run_verification_in_background, verification.id, pdf_path
    )

    return VerificationResponse.model_validate(verification)


@router.get(
    "/",
    response_model=VerificationListResponse,
    summary="List user verifications",
)
async def list_verifications(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> VerificationListResponse:
    """Get list of user's verifications."""
    verifications = await verification_repository.get_by_user(
        db, current_user.id, skip=skip, limit=limit
    )
    total = await verification_repository.count_by_user(db, current_user.id)

    return VerificationListResponse(
        items=[VerificationResponse.model_validate(v) for v in verifications],
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
    )


@router.get(
    "/summary",
    response_model=VerificationSummaryResponse,
    summary="Get verification summary",
)
async def get_summary(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> VerificationSummaryResponse:
    """Get summary statistics for user's verifications."""
    from datetime import datetime, timedelta
    from sqlalchemy import func, select

    # Total count
    total = await verification_repository.count_by_user(db, current_user.id)

    # Status counts
    result = await db.execute(
        select(Verification.status, func.count())
        .where(Verification.user_id == current_user.id)
        .group_by(Verification.status)
    )
    status_counts = {status.value: count for status, count in result.all()}

    # This month count
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(func.count())
        .select_from(Verification)
        .where(
            Verification.user_id == current_user.id,
            Verification.created_at >= month_start,
        )
    )
    this_month = result.scalar_one()

    return VerificationSummaryResponse(
        total=total,
        completed=status_counts.get("completed", 0),
        pending=status_counts.get("pending", 0) + status_counts.get("in_progress", 0),
        failed=status_counts.get("failed", 0),
        this_month=this_month,
    )


@router.get(
    "/{verification_id}",
    response_model=VerificationDetailResponse,
    summary="Get verification details",
)
async def get_verification(
    verification_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> VerificationDetailResponse:
    """Get detailed verification information including findings."""
    verification = await verification_repository.get_by_id_with_details(db, verification_id)

    if not verification:
        raise NotFoundError("Verification not found")

    if verification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this verification",
        )

    return VerificationDetailResponse.model_validate(verification)


@router.delete(
    "/{verification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete verification",
)
async def delete_verification(
    verification_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a verification and its associated data."""
    verification = await verification_repository.get_by_id(db, verification_id)

    if not verification:
        raise NotFoundError("Verification not found")

    if verification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this verification",
        )

    await verification_repository.delete(db, id=verification_id)
