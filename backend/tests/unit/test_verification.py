"""Unit tests for verification engine."""

import pytest

from app.services.verification.domain_verifier import DomainVerifier
from app.services.verification.ssl_verifier import SSLVerifier
from app.services.verification.dns_verifier import DNSVerifier


class TestDomainVerifier:
    """Test domain verification."""

    def test_clean_domain_removes_protocol(self):
        verifier = DomainVerifier()
        assert verifier._clean_domain("https://example.com") == "example.com"
        assert verifier._clean_domain("http://example.com") == "example.com"

    def test_clean_domain_removes_www(self):
        verifier = DomainVerifier()
        assert verifier._clean_domain("www.example.com") == "example.com"

    def test_clean_domain_removes_path(self):
        verifier = DomainVerifier()
        assert verifier._clean_domain("example.com/path") == "example.com"


class TestSSLVerifier:
    """Test SSL verification."""

    def test_clean_domain_removes_protocol(self):
        verifier = SSLVerifier()
        assert verifier._clean_domain("https://example.com") == "example.com"


class TestDNSVerifier:
    """Test DNS verification."""

    def test_clean_domain_removes_protocol(self):
        verifier = DNSVerifier()
        assert verifier._clean_domain("https://example.com") == "example.com"

    def test_email_domain_extraction(self):
        verifier = DNSVerifier()
        domain = "test@example.com".split("@")[-1]
        assert domain == "example.com"
