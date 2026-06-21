"""Report generation service using ReportLab."""

from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import List, Optional
from uuid import UUID, uuid4

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import get_logger, get_settings
from app.models.report import Report, ReportStatus
from app.models.verification import Verification
from app.models.verification_finding import FindingSeverity, VerificationFinding
from app.services.verification_service import verification_service

logger = get_logger(__name__)


class ReportService:
    """Generate professional PDF verification reports."""

    def __init__(self):
        self.settings = get_settings()

    async def generate_report(
        self,
        db: AsyncSession,
        verification_id: UUID,
        user_id: UUID,
        title: Optional[str] = None,
    ) -> Report:
        """Generate a PDF report for a verification."""
        from app.repositories import verification_repository

        # Get verification with findings
        verification = await verification_repository.get_by_id_with_details(db, verification_id)

        if not verification:
            raise ValueError("Verification not found")

        if verification.user_id != user_id:
            raise ValueError("Not authorized to generate report for this verification")

        # Generate report filename
        report_id = uuid4()
        filename = f"trustcheck_report_{report_id}.pdf"
        reports_dir = self.settings.upload_path / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        file_path = reports_dir / filename

        # Create report record
        report = Report(
            id=report_id,
            verification_id=verification_id,
            user_id=user_id,
            title=title or f"Verification Report - {verification.company_name or 'Unknown Company'}",
            file_path=str(file_path),
            file_size_bytes=0,  # Will be updated after generation
            status=ReportStatus.GENERATING,
        )
        db.add(report)
        await db.flush()

        try:
            # Generate PDF
            pdf_content = self._generate_pdf(verification, report.title)

            # Write to file
            with open(file_path, "wb") as f:
                f.write(pdf_content)

            # Update report status
            report.status = ReportStatus.COMPLETED
            report.file_size_bytes = len(pdf_content)

            logger.info(
                "Report generated successfully",
                report_id=str(report_id),
                verification_id=str(verification_id),
            )

        except Exception as e:
            logger.error(f"Report generation failed: {e}", report_id=str(report_id))
            report.status = ReportStatus.FAILED
            report.error_message = str(e)

        await db.flush()
        # Load server-side defaults (created_at/updated_at) so the response can
        # be serialized without triggering a lazy DB load in a sync context.
        await db.refresh(report)
        return report

    def _generate_pdf(
        self,
        verification: Verification,
        title: str,
    ) -> bytes:
        """Generate PDF content."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18,
        )

        # Container for elements
        elements = []

        # Styles
        styles = getSampleStyleSheet()
        title_style = styles["Heading1"]
        heading_style = styles["Heading2"]
        normal_style = styles["Normal"]
        normal_style.fontSize = 10

        # Custom styles
        custom_title = ParagraphStyle(
            "CustomTitle",
            parent=styles["Heading1"],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.HexColor("#1e40af"),
        )

        # Title
        elements.append(Paragraph("TrustCheck Verification Report", custom_title))
        elements.append(Spacer(1, 20))

        # Report metadata
        meta_data = [
            ["Report Title:", title],
            ["Generated:", datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")],
            ["Verification ID:", str(verification.id)],
            ["Status:", verification.status.value],
        ]

        if verification.company_name:
            meta_data.append(["Company:", verification.company_name])
        if verification.target_url:
            meta_data.append(["Website:", verification.target_url])
        if verification.recruiter_email:
            meta_data.append(["Recruiter Email:", verification.recruiter_email])

        meta_table = Table(meta_data, colWidths=[2 * inch, 4 * inch])
        meta_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 30))

        # Summary section
        elements.append(Paragraph("Executive Summary", heading_style))
        elements.append(Spacer(1, 12))

        # Calculate findings summary
        findings = verification.findings or []
        passed = len([f for f in findings if f.severity == FindingSeverity.PASSED])
        warnings = len([f for f in findings if f.severity == FindingSeverity.WARNING])
        critical = len([f for f in findings if f.severity == FindingSeverity.CRITICAL])
        info = len([f for f in findings if f.severity == FindingSeverity.INFO])

        summary_data = [
            ["Total Checks:", str(len(findings))],
            ["Passed:", str(passed)],
            ["Warnings:", str(warnings)],
            ["Critical:", str(critical)],
            ["Info:", str(info)],
        ]

        summary_table = Table(summary_data, colWidths=[2 * inch, 2 * inch])
        summary_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            # Color code the counts
            ("TEXTCOLOR", (1, 1), (1, 1), colors.green),
            ("TEXTCOLOR", (1, 2), (1, 2), colors.orange),
            ("TEXTCOLOR", (1, 3), (1, 3), colors.red),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 30))

        # Findings section
        if findings:
            elements.append(Paragraph("Detailed Findings", heading_style))
            elements.append(Spacer(1, 12))

            # Group findings by category
            findings_by_category = {}
            for finding in findings:
                cat = finding.category.value
                if cat not in findings_by_category:
                    findings_by_category[cat] = []
                findings_by_category[cat].append(finding)

            for category, cat_findings in findings_by_category.items():
                elements.append(Paragraph(f"{category.upper()} Checks", styles["Heading3"]))
                elements.append(Spacer(1, 8))

                for finding in cat_findings:
                    # Severity badge
                    severity_color = self._get_severity_color(finding.severity)

                    finding_text = f"""
                    <b>{finding.title}</b><br/>
                    <font size="9" color="{severity_color}"><b>{finding.severity.value.upper()}</b></font><br/>
                    <font size="9">{finding.description or ''}</font>
                    """
                    elements.append(Paragraph(finding_text, normal_style))
                    elements.append(Spacer(1, 12))

        # Footer
        elements.append(Spacer(1, 40))
        elements.append(Paragraph(
            "<font size='8' color='grey'>Generated by TrustCheck - Evidence-Based Verification Platform</font>",
            normal_style,
        ))

        # Build PDF
        doc.build(elements)
        pdf_content = buffer.getvalue()
        buffer.close()

        return pdf_content

    def _get_severity_color(self, severity: FindingSeverity) -> str:
        """Get color for severity level."""
        colors_map = {
            FindingSeverity.PASSED: "#16a34a",  # green
            FindingSeverity.INFO: "#2563eb",    # blue
            FindingSeverity.WARNING: "#ea580c", # orange
            FindingSeverity.CRITICAL: "#dc2626", # red
        }
        return colors_map.get(severity, "#000000")


# Singleton instance
report_service = ReportService()
