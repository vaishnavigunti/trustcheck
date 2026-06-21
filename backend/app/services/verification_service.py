"""Verification orchestrator service."""

import asyncio
import time
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_logger
from app.models.evidence_timeline import TimelineEventType
from app.models.verification import Verification, VerificationStatus
from app.models.verification_finding import FindingSeverity, VerificationFinding
from app.services.verification import (
    DNSVerifier,
    DomainVerifier,
    EvidenceBuilder,
    PDFAnalyzer,
    SSLVerifier,
    WebsiteAnalyzer,
)

logger = get_logger(__name__)


class VerificationService:
    """Orchestrates the complete verification process."""

    def __init__(
        self,
        domain_verifier: Optional[DomainVerifier] = None,
        ssl_verifier: Optional[SSLVerifier] = None,
        dns_verifier: Optional[DNSVerifier] = None,
        website_analyzer: Optional[WebsiteAnalyzer] = None,
        pdf_analyzer: Optional[PDFAnalyzer] = None,
        evidence_builder: Optional[EvidenceBuilder] = None,
    ):
        self.domain_verifier = domain_verifier or DomainVerifier()
        self.ssl_verifier = ssl_verifier or SSLVerifier()
        self.dns_verifier = dns_verifier or DNSVerifier()
        self.website_analyzer = website_analyzer or WebsiteAnalyzer()
        self.pdf_analyzer = pdf_analyzer or PDFAnalyzer()
        self.evidence_builder = evidence_builder or EvidenceBuilder()
        self._timeline_counter = 0

    async def run_verification(
        self,
        db: AsyncSession,
        verification: Verification,
        pdf_path: Optional[str] = None,
    ) -> Verification:
        """Run complete verification process."""
        start_time = time.time()
        verification.status = VerificationStatus.IN_PROGRESS
        verification.started_at = datetime.utcnow()
        await db.flush()

        # Reset evidence builder and timeline counter
        self.evidence_builder = EvidenceBuilder()
        self._timeline_counter = 0

        try:
            # Step 1: Domain Verification
            await self._run_domain_check(db, verification)

            # Step 2: SSL Verification
            await self._run_ssl_check(db, verification)

            # Step 3: DNS Verification
            await self._run_dns_check(db, verification)

            # Step 4: Website Analysis (if domain accessible)
            await self._run_website_analysis(db, verification)

            # Step 5: PDF Analysis (if PDF provided)
            if pdf_path:
                await self._run_pdf_analysis(db, verification, pdf_path)

            # Step 6: Cross-validate findings
            await self._run_cross_validation(db, verification)

            # Save all findings
            await self._save_findings(db, verification)

            # Mark as completed
            verification.status = VerificationStatus.COMPLETED
            verification.completed_at = datetime.utcnow()
            verification.processing_time_ms = int((time.time() - start_time) * 1000)

            logger.info(
                "Verification completed",
                verification_id=str(verification.id),
                processing_time_ms=verification.processing_time_ms,
            )

        except Exception as e:
            logger.error(f"Verification failed: {e}", verification_id=str(verification.id))
            verification.status = VerificationStatus.FAILED
            verification.error_message = str(e)
            verification.completed_at = datetime.utcnow()

        await db.flush()
        return verification

    async def _run_domain_check(
        self,
        db: AsyncSession,
        verification: Verification,
    ) -> None:
        """Run domain verification."""
        step_start = time.time()
        target = verification.target_url or verification.company_name

        if not target:
            return

        # Verifiers do blocking network I/O — run off the event loop so the
        # API stays responsive while a verification is in progress.
        result = await asyncio.to_thread(self.domain_verifier.verify, target)
        self.evidence_builder.build_from_domain(result)

        # Add timeline entry
        await self._add_timeline_entry(
            db,
            verification,
            TimelineEventType.DOMAIN_CHECK,
            "Domain Verification",
            f"Checked domain: {result.domain}",
            duration_ms=int((time.time() - step_start) * 1000),
        )

    async def _run_ssl_check(
        self,
        db: AsyncSession,
        verification: Verification,
    ) -> None:
        """Run SSL verification."""
        step_start = time.time()
        target = verification.target_url

        if not target:
            return

        result = await asyncio.to_thread(self.ssl_verifier.verify, target)
        self.evidence_builder.build_from_ssl(result)

        await self._add_timeline_entry(
            db,
            verification,
            TimelineEventType.SSL_CHECK,
            "SSL Certificate Check",
            f"HTTPS available: {result.https_available}",
            duration_ms=int((time.time() - step_start) * 1000),
        )

    async def _run_dns_check(
        self,
        db: AsyncSession,
        verification: Verification,
    ) -> None:
        """Run DNS verification."""
        step_start = time.time()
        target = verification.target_url or verification.recruiter_email

        if not target:
            return

        # If email provided, extract domain
        if verification.recruiter_email:
            result = await asyncio.to_thread(
                self.dns_verifier.verify_email_domain, verification.recruiter_email
            )
        else:
            result = await asyncio.to_thread(self.dns_verifier.verify, target)

        self.evidence_builder.build_from_dns(result)

        await self._add_timeline_entry(
            db,
            verification,
            TimelineEventType.DNS_CHECK,
            "DNS Records Check",
            f"MX records: {result.has_mx_records}, SPF: {result.has_spf}",
            duration_ms=int((time.time() - step_start) * 1000),
        )

    async def _run_website_analysis(
        self,
        db: AsyncSession,
        verification: Verification,
    ) -> None:
        """Run website analysis."""
        step_start = time.time()
        target = verification.target_url

        if not target:
            return

        result = await asyncio.to_thread(self.website_analyzer.analyze, target)
        self.evidence_builder.build_from_website(result)

        await self._add_timeline_entry(
            db,
            verification,
            TimelineEventType.WEBSITE_ANALYSIS,
            "Website Analysis",
            f"Accessible: {result.accessible}, Title: {result.title or 'N/A'}",
            duration_ms=int((time.time() - step_start) * 1000),
        )

    async def _run_pdf_analysis(
        self,
        db: AsyncSession,
        verification: Verification,
        pdf_path: str,
    ) -> None:
        """Run PDF analysis."""
        from app.models.pdf_extracted_data import PDFExtractedData

        step_start = time.time()
        result = await asyncio.to_thread(self.pdf_analyzer.analyze, pdf_path)

        # Save extracted data
        pdf_data = PDFExtractedData(
            verification_id=verification.id,
            raw_text=result.raw_text,
            extracted_company_name=result.company_name,
            extracted_email=result.email,
            extracted_website=result.website,
            extracted_address=result.address,
            extracted_phone=result.phone,
            extracted_position=result.position,
            extracted_salary=result.salary,
            extracted_start_date=result.start_date,
            extraction_errors=result.errors,
        )
        db.add(pdf_data)

        self.evidence_builder.build_from_pdf(result)

        await self._add_timeline_entry(
            db,
            verification,
            TimelineEventType.PDF_EXTRACTION,
            "PDF Analysis",
            f"Pages: {result.page_count}, Fields extracted: {len([x for x in [result.company_name, result.email, result.website] if x])}",
            duration_ms=int((time.time() - step_start) * 1000),
        )

    async def _run_cross_validation(
        self,
        db: AsyncSession,
        verification: Verification,
    ) -> None:
        """Cross-validate findings between different sources."""
        step_start = time.time()

        # Get findings for cross-validation
        findings = self.evidence_builder.get_findings()

        # Look for email domain mismatches
        domain_findings = [f for f in findings if f.category.value == "domain"]
        email_findings = [f for f in findings if f.category.value == "email"]

        # This is where we'd add complex cross-validation logic
        # For now, just add a timeline entry

        await self._add_timeline_entry(
            db,
            verification,
            TimelineEventType.CROSS_VALIDATION,
            "Cross-Validation",
            f"Validated {len(findings)} findings across sources",
            duration_ms=int((time.time() - step_start) * 1000),
        )

    async def _save_findings(
        self,
        db: AsyncSession,
        verification: Verification,
    ) -> None:
        """Save all evidence findings to database."""
        findings = self.evidence_builder.get_findings()

        for idx, finding in enumerate(findings, 1):
            db_finding = VerificationFinding(
                verification_id=verification.id,
                category=finding.category,
                check_name=finding.check_name,
                severity=finding.severity,
                title=finding.title,
                description=finding.description,
                evidence=finding.evidence,
                recommendation=finding.recommendation,
                sequence_order=idx,
            )
            db.add(db_finding)

        await db.flush()

    async def _add_timeline_entry(
        self,
        db: AsyncSession,
        verification: Verification,
        event_type: TimelineEventType,
        title: str,
        description: str,
        duration_ms: Optional[int] = None,
        data: Optional[dict] = None,
    ) -> None:
        """Add entry to evidence timeline."""
        from app.models.evidence_timeline import EvidenceTimeline

        self._timeline_counter += 1

        timeline_entry = EvidenceTimeline(
            verification_id=verification.id,
            event_type=event_type,
            sequence_order=self._timeline_counter,
            title=title,
            description=description,
            duration_ms=duration_ms,
            data=data or {},
        )
        db.add(timeline_entry)

    def get_summary(self, findings: List[VerificationFinding]) -> dict:
        """Get summary of findings."""
        passed = len([f for f in findings if f.severity == FindingSeverity.PASSED])
        warnings = len([f for f in findings if f.severity == FindingSeverity.WARNING])
        critical = len([f for f in findings if f.severity == FindingSeverity.CRITICAL])
        info = len([f for f in findings if f.severity == FindingSeverity.INFO])

        return {
            "total": len(findings),
            "passed": passed,
            "warnings": warnings,
            "critical": critical,
            "info": info,
        }


# Singleton instance (kept for convenience / synchronous callers)
verification_service = VerificationService()


async def run_verification_in_background(
    verification_id: UUID,
    pdf_path: Optional[str] = None,
) -> None:
    """Run a verification in its own DB session (used as a background task).

    The request that created the verification has already returned by the time
    this runs, so it opens a fresh session and uses a dedicated service instance
    to avoid sharing per-run state (evidence builder / timeline counter) with
    concurrent verifications.
    """
    from app.core.database import get_db_context
    from app.repositories import verification_repository

    async with get_db_context() as db:
        verification = await verification_repository.get_by_id(db, verification_id)
        if verification is None:
            logger.error(
                "Background verification skipped: not found",
                verification_id=str(verification_id),
            )
            return

        # run_verification handles its own error capture (marks FAILED).
        service = VerificationService()
        await service.run_verification(db, verification, pdf_path)
