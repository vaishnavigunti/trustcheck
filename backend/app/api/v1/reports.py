"""Reports API routes."""

from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.database import get_db as get_db_session
from app.core.exceptions import NotFoundError
from app.core.security import create_public_report_token, verify_token
from app.models.report import Report
from app.models.shared_report import SharedReport
from app.models.user import User
from app.schemas.report import (
    ReportCreateRequest,
    ReportListResponse,
    ReportResponse,
    SharedReportCreateRequest,
    SharedReportResponse,
)
from app.services.report_service import report_service

router = APIRouter()


@router.post(
    "/",
    response_model=ReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate report",
)
async def create_report(
    request: Request,
    data: ReportCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ReportResponse:
    """Generate a PDF report for a verification."""
    report = await report_service.generate_report(
        db,
        verification_id=data.verification_id,
        user_id=current_user.id,
        title=data.title,
    )
    return ReportResponse.model_validate(report)


@router.get(
    "/",
    response_model=ReportListResponse,
    summary="List user reports",
)
async def list_reports(
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ReportListResponse:
    """Get list of user's generated reports."""
    from sqlalchemy import desc, select

    result = await db.execute(
        select(Report)
        .where(Report.user_id == current_user.id)
        .order_by(desc(Report.created_at))
    )
    reports = list(result.scalars().all())

    return ReportListResponse(
        items=[ReportResponse.model_validate(r) for r in reports],
        total=len(reports),
    )


@router.get(
    "/{report_id}",
    response_model=ReportResponse,
    summary="Get report details",
)
async def get_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> ReportResponse:
    """Get report details."""
    from sqlalchemy import select

    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise NotFoundError("Report not found")

    if report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this report",
        )

    return ReportResponse.model_validate(report)


@router.get(
    "/{report_id}/download",
    summary="Download report PDF",
)
async def download_report(
    report_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> FileResponse:
    """Download report PDF file."""
    from sqlalchemy import select

    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise NotFoundError("Report not found")

    if report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to download this report",
        )

    if report.status.value != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Report is not ready for download",
        )

    file_path = Path(report.file_path)
    if not file_path.exists():
        raise NotFoundError("Report file not found")

    return FileResponse(
        path=str(file_path),
        filename=f"TrustCheck_Report_{report_id}.pdf",
        media_type="application/pdf",
    )


@router.post(
    "/{report_id}/share",
    response_model=SharedReportResponse,
    summary="Create shareable link",
)
async def share_report(
    report_id: UUID,
    data: SharedReportCreateRequest,
    db: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
    request: Request = None,
) -> SharedReportResponse:
    """Create a public shareable link for a report."""
    from datetime import datetime, timedelta
    from sqlalchemy import select

    # Verify report exists and belongs to user
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise NotFoundError("Report not found")

    if report.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to share this report",
        )

    # Create signed token
    token = create_public_report_token(str(report_id), expires_delta=timedelta(days=data.expires_days))

    # Create shared report record
    shared = SharedReport(
        report_id=report_id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(days=data.expires_days),
        created_by_ip=request.client.host if request else None,
    )
    db.add(shared)
    await db.flush()

    # Generate share URL
    base_url = str(request.base_url) if request else ""
    share_url = f"{base_url}public/reports/{token}"

    return SharedReportResponse(
        id=shared.id,
        report_id=shared.report_id,
        token=shared.token,
        expires_at=shared.expires_at,
        share_url=share_url,
        accessed_count=shared.accessed_count,
        is_active=shared.is_active,
    )


@router.get(
    "/public/{token}",
    summary="Access shared report",
)
async def access_shared_report(
    token: str,
    db: AsyncSession = Depends(get_db_session),
) -> FileResponse:
    """Access a report via public share token."""
    from sqlalchemy import select

    # Verify token
    payload = verify_token(token, expected_type="public_report")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired share link",
        )

    report_id = payload.get("report_id")

    # Find shared report record
    result = await db.execute(
        select(SharedReport).where(
            SharedReport.token == token,
            SharedReport.revoked_at.is_(None),
        )
    )
    shared = result.scalar_one_or_none()

    if not shared or not shared.is_active:
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Share link has expired or been revoked",
        )

    # Update access count
    shared.record_access()

    # Get report
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()

    if not report or report.status.value != "completed":
        raise NotFoundError("Report not found or not ready")

    file_path = Path(report.file_path)
    if not file_path.exists():
        raise NotFoundError("Report file not found")

    return FileResponse(
        path=str(file_path),
        filename=f"TrustCheck_Report.pdf",
        media_type="application/pdf",
    )
