"""Evidence builder module for aggregating verification findings."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.core import get_logger
from app.models.verification_finding import FindingCategory, FindingSeverity
from app.services.verification.dns_verifier import DNSVerificationResult
from app.services.verification.domain_verifier import DomainVerificationResult
from app.services.verification.pdf_analyzer import PDFAnalysisResult
from app.services.verification.ssl_verifier import SSLVerificationResult
from app.services.verification.website_analyzer import WebsiteAnalysisResult

logger = get_logger(__name__)


class EvidenceFinding:
    """A single evidence finding."""

    def __init__(
        self,
        category: FindingCategory,
        check_name: str,
        severity: FindingSeverity,
        title: str,
        description: Optional[str] = None,
        evidence: Optional[Dict] = None,
        recommendation: Optional[str] = None,
    ):
        self.category = category
        self.check_name = check_name
        self.severity = severity
        self.title = title
        self.description = description
        self.evidence = evidence or {}
        self.recommendation = recommendation

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "category": self.category.value,
            "check_name": self.check_name,
            "severity": self.severity.value,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "recommendation": self.recommendation,
        }


class EvidenceBuilder:
    """Build evidence findings from verification results."""

    def __init__(self):
        self.findings: List[EvidenceFinding] = []
        self.sequence = 0

    def add_finding(self, finding: EvidenceFinding) -> None:
        """Add a finding to the evidence."""
        self.sequence += 1
        self.findings.append(finding)

    def build_from_domain(
        self,
        result: DomainVerificationResult,
    ) -> None:
        """Build findings from domain verification."""
        if result.error and not result.exists:
            self.add_finding(EvidenceFinding(
                category=FindingCategory.DOMAIN,
                check_name="domain_resolution",
                severity=FindingSeverity.CRITICAL,
                title="Domain Does Not Resolve",
                description=result.error,
                evidence={"domain": result.domain},
                recommendation="Verify the domain name is correct and the website is accessible",
            ))
            return

        if result.error:
            self.add_finding(EvidenceFinding(
                category=FindingCategory.DOMAIN,
                check_name="whois_lookup",
                severity=FindingSeverity.WARNING,
                title="WHOIS Lookup Failed",
                description=result.error,
                evidence={"domain": result.domain},
                recommendation="WHOIS data may be unavailable due to privacy restrictions",
            ))

        # Domain exists
        self.add_finding(EvidenceFinding(
            category=FindingCategory.DOMAIN,
            check_name="domain_exists",
            severity=FindingSeverity.PASSED,
            title="Domain Resolves Successfully",
            description=f"The domain {result.domain} resolves to an IP address",
            evidence={"domain": result.domain},
        ))

        # Registration date
        if result.registration_date:
            age_days = result.domain_age_days or 0
            if age_days < 30:
                severity = FindingSeverity.WARNING
                title = f"Domain Registered Recently ({age_days} days ago)"
                recommendation = "Recently registered domains may be less established"
            elif age_days < 365:
                severity = FindingSeverity.INFO
                title = f"Domain Registered {age_days} days ago"
                recommendation = None
            else:
                severity = FindingSeverity.PASSED
                years = age_days // 365
                title = f"Domain Established ({years}+ years old)"
                recommendation = None

            self.add_finding(EvidenceFinding(
                category=FindingCategory.DOMAIN,
                check_name="domain_age",
                severity=severity,
                title=title,
                description=f"Domain was registered on {result.registration_date.strftime('%Y-%m-%d')}",
                evidence={
                    "registration_date": result.registration_date.isoformat(),
                    "age_days": age_days,
                },
                recommendation=recommendation,
            ))
        else:
            self.add_finding(EvidenceFinding(
                category=FindingCategory.DOMAIN,
                check_name="registration_date",
                severity=FindingSeverity.INFO,
                title="Registration Date Unavailable",
                description="WHOIS data does not include registration date (may be redacted)",
                evidence={},
            ))

        # Expiration date
        if result.expiration_date:
            days_left = result.days_until_expiration or 0
            if days_left < 30:
                severity = FindingSeverity.WARNING
                title = f"Domain Expires Soon ({days_left} days)"
            elif days_left < 90:
                severity = FindingSeverity.INFO
                title = f"Domain Expires in {days_left} days"
            else:
                severity = FindingSeverity.PASSED
                title = "Domain Registration Valid"

            self.add_finding(EvidenceFinding(
                category=FindingCategory.DOMAIN,
                check_name="expiration_date",
                severity=severity,
                title=title,
                description=f"Domain expires on {result.expiration_date.strftime('%Y-%m-%d')}",
                evidence={
                    "expiration_date": result.expiration_date.isoformat(),
                    "days_until_expiration": days_left,
                },
            ))

    def build_from_ssl(self, result: SSLVerificationResult) -> None:
        """Build findings from SSL verification."""
        if not result.https_available:
            self.add_finding(EvidenceFinding(
                category=FindingCategory.SSL,
                check_name="https_available",
                severity=FindingSeverity.CRITICAL,
                title="HTTPS Not Available",
                description="The website does not support HTTPS connections",
                evidence={"domain": result.domain},
                recommendation="Secure websites should use HTTPS",
            ))
            return

        self.add_finding(EvidenceFinding(
            category=FindingCategory.SSL,
            check_name="https_available",
            severity=FindingSeverity.PASSED,
            title="HTTPS Available",
            description="The website supports secure HTTPS connections",
            evidence={"domain": result.domain},
        ))

        if result.error:
            self.add_finding(EvidenceFinding(
                category=FindingCategory.SSL,
                check_name="ssl_certificate",
                severity=FindingSeverity.WARNING,
                title="SSL Certificate Issue",
                description=result.error,
                evidence={},
            ))
            return

        if result.is_valid:
            days_left = result.days_until_expiry or 0
            if days_left < 30:
                severity = FindingSeverity.WARNING
                title = f"SSL Certificate Expires Soon ({days_left} days)"
            else:
                severity = FindingSeverity.PASSED
                title = "SSL Certificate Valid"

            self.add_finding(EvidenceFinding(
                category=FindingCategory.SSL,
                check_name="ssl_valid",
                severity=severity,
                title=title,
                description=f"Certificate issued by: {result.issuer or 'Unknown'}",
                evidence={
                    "issuer": result.issuer,
                    "valid_until": result.valid_until.isoformat() if result.valid_until else None,
                    "days_until_expiry": days_left,
                },
            ))
        else:
            self.add_finding(EvidenceFinding(
                category=FindingCategory.SSL,
                check_name="ssl_valid",
                severity=FindingSeverity.CRITICAL,
                title="SSL Certificate Invalid or Expired",
                description="The SSL certificate is not valid",
                evidence={},
                recommendation="Ensure the website has a valid SSL certificate",
            ))

    def build_from_dns(self, result: DNSVerificationResult) -> None:
        """Build findings from DNS verification."""
        # MX Records
        if result.has_mx_records:
            self.add_finding(EvidenceFinding(
                category=FindingCategory.DNS,
                check_name="mx_records",
                severity=FindingSeverity.PASSED,
                title="Email Server Records Found",
                description=f"Found {len(result.mx_records)} MX record(s)",
                evidence={"mx_records": result.mx_records},
            ))
        else:
            self.add_finding(EvidenceFinding(
                category=FindingCategory.DNS,
                check_name="mx_records",
                severity=FindingSeverity.INFO,
                title="No Email Server Records",
                description="No MX records found for this domain",
                evidence={},
                recommendation="This domain may not be configured to receive email",
            ))

        # SPF
        if result.has_spf:
            self.add_finding(EvidenceFinding(
                category=FindingCategory.DNS,
                check_name="spf_record",
                severity=FindingSeverity.PASSED,
                title="SPF Record Found",
                description="Domain has SPF record for email authentication",
                evidence={"spf": result.spf_record},
            ))
        else:
            self.add_finding(EvidenceFinding(
                category=FindingCategory.DNS,
                check_name="spf_record",
                severity=FindingSeverity.WARNING,
                title="No SPF Record",
                description="Domain does not have SPF record configured",
                evidence={},
                recommendation="SPF records help prevent email spoofing",
            ))

        # DMARC
        if result.has_dmarc:
            self.add_finding(EvidenceFinding(
                category=FindingCategory.DNS,
                check_name="dmarc_record",
                severity=FindingSeverity.PASSED,
                title="DMARC Record Found",
                description="Domain has DMARC policy for email authentication",
                evidence={"dmarc": result.dmarc_record},
            ))
        else:
            self.add_finding(EvidenceFinding(
                category=FindingCategory.DNS,
                check_name="dmarc_record",
                severity=FindingSeverity.INFO,
                title="No DMARC Record",
                description="Domain does not have DMARC policy configured",
                evidence={},
            ))

    def build_from_website(self, result: WebsiteAnalysisResult) -> None:
        """Build findings from website analysis."""
        if not result.accessible:
            self.add_finding(EvidenceFinding(
                category=FindingCategory.WEBSITE,
                check_name="website_accessible",
                severity=FindingSeverity.CRITICAL,
                title="Website Not Accessible",
                description=result.error or "Could not access the website",
                evidence={"url": result.url},
            ))
            return

        self.add_finding(EvidenceFinding(
            category=FindingCategory.WEBSITE,
            check_name="website_accessible",
            severity=FindingSeverity.PASSED,
            title="Website Accessible",
            description=f"Website responded with status {result.status_code}",
            evidence={
                "url": result.url,
                "status_code": result.status_code,
                "response_time_ms": result.response_time_ms,
            },
        ))

        # Title
        if result.title:
            self.add_finding(EvidenceFinding(
                category=FindingCategory.WEBSITE,
                check_name="page_title",
                severity=FindingSeverity.INFO,
                title="Page Title Found",
                description=f"Website title: {result.title}",
                evidence={"title": result.title},
            ))

        # Important pages
        pages = [
            ("about", result.has_about_page, "About Page"),
            ("contact", result.has_contact_page, "Contact Page"),
            ("privacy", result.has_privacy_policy, "Privacy Policy"),
            ("terms", result.has_terms_page, "Terms of Service"),
        ]

        for key, exists, label in pages:
            if exists:
                self.add_finding(EvidenceFinding(
                    category=FindingCategory.WEBSITE,
                    check_name=f"has_{key}_page",
                    severity=FindingSeverity.PASSED,
                    title=f"{label} Present",
                    description=f"Website has a {label.lower()}",
                    evidence={},
                ))
            else:
                self.add_finding(EvidenceFinding(
                    category=FindingCategory.WEBSITE,
                    check_name=f"has_{key}_page",
                    severity=FindingSeverity.WARNING,
                    title=f"{label} Not Found",
                    description=f"Could not find {label.lower()} on the website",
                    evidence={},
                    recommendation=f"Professional websites typically have a {label.lower()}",
                ))

        # Social links
        if result.social_links:
            self.add_finding(EvidenceFinding(
                category=FindingCategory.WEBSITE,
                check_name="social_links",
                severity=FindingSeverity.INFO,
                title=f"Found {len(result.social_links)} Social Media Link(s)",
                description="Website links to social media profiles",
                evidence={"social_links": result.social_links[:5]},
            ))

    def build_from_pdf(self, result: PDFAnalysisResult) -> None:
        """Build findings from PDF analysis."""
        if not result.success:
            self.add_finding(EvidenceFinding(
                category=FindingCategory.PDF,
                check_name="pdf_analysis",
                severity=FindingSeverity.WARNING,
                title="PDF Analysis Failed",
                description=result.errors[0] if result.errors else "Could not analyze PDF",
                evidence={},
            ))
            return

        self.add_finding(EvidenceFinding(
            category=FindingCategory.PDF,
            check_name="pdf_analysis",
            severity=FindingSeverity.PASSED,
            title="PDF Analyzed Successfully",
            description=f"Extracted data from {result.page_count} page(s)",
            evidence={"page_count": result.page_count},
        ))

        # Extracted fields
        fields = [
            ("company_name", result.company_name, "Company Name"),
            ("email", result.email, "Email Address"),
            ("website", result.website, "Website"),
            ("position", result.position, "Job Position"),
            ("salary", result.salary, "Salary Information"),
            ("start_date", result.start_date, "Start Date"),
        ]

        for key, value, label in fields:
            if value:
                self.add_finding(EvidenceFinding(
                    category=FindingCategory.PDF,
                    check_name=f"pdf_{key}",
                    severity=FindingSeverity.INFO,
                    title=f"{label} Extracted",
                    description=f"Found {label}: {value}",
                    evidence={key: value},
                ))

    def get_findings(self) -> List[EvidenceFinding]:
        """Get all findings."""
        return self.findings

    def to_dict_list(self) -> List[Dict]:
        """Convert all findings to dictionary list."""
        return [f.to_dict() for f in self.findings]


# Singleton instance
evidence_builder = EvidenceBuilder()
