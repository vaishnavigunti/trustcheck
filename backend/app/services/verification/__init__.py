"""Verification engine modules."""

from app.services.verification.dns_verifier import DNSVerificationResult, DNSVerifier, dns_verifier
from app.services.verification.domain_verifier import (
    DomainVerificationResult,
    DomainVerifier,
    domain_verifier,
)
from app.services.verification.evidence_builder import (
    EvidenceBuilder,
    EvidenceFinding,
    evidence_builder,
)
from app.services.verification.pdf_analyzer import PDFAnalysisResult, PDFAnalyzer, pdf_analyzer
from app.services.verification.ssl_verifier import SSLVerificationResult, SSLVerifier, ssl_verifier
from app.services.verification.website_analyzer import (
    WebsiteAnalysisResult,
    WebsiteAnalyzer,
    website_analyzer,
)

__all__ = [
    # Domain
    "DomainVerificationResult",
    "DomainVerifier",
    "domain_verifier",
    # SSL
    "SSLVerificationResult",
    "SSLVerifier",
    "ssl_verifier",
    # DNS
    "DNSVerificationResult",
    "DNSVerifier",
    "dns_verifier",
    # Website
    "WebsiteAnalysisResult",
    "WebsiteAnalyzer",
    "website_analyzer",
    # PDF
    "PDFAnalysisResult",
    "PDFAnalyzer",
    "pdf_analyzer",
    # Evidence
    "EvidenceBuilder",
    "EvidenceFinding",
    "evidence_builder",
]
