"""SSL certificate verification module."""

import socket
import ssl
from datetime import datetime
from typing import Dict, List, Optional

from app.core import get_logger, get_settings
from app.core.config import Settings

logger = get_logger(__name__)


class SSLVerificationResult:
    """Result of SSL verification."""

    def __init__(
        self,
        domain: str,
        https_available: bool,
        is_valid: bool = False,
        issuer: Optional[str] = None,
        subject: Optional[str] = None,
        valid_from: Optional[datetime] = None,
        valid_until: Optional[datetime] = None,
        serial_number: Optional[str] = None,
        fingerprint: Optional[str] = None,
        alt_names: Optional[List[str]] = None,
        error: Optional[str] = None,
    ):
        self.domain = domain
        self.https_available = https_available
        self.is_valid = is_valid
        self.issuer = issuer
        self.subject = subject
        self.valid_from = valid_from
        self.valid_until = valid_until
        self.serial_number = serial_number
        self.fingerprint = fingerprint
        self.alt_names = alt_names or []
        self.error = error

    @property
    def days_until_expiry(self) -> Optional[int]:
        """Calculate days until certificate expires."""
        if self.valid_until:
            return (self.valid_until - datetime.utcnow()).days
        return None

    @property
    def is_expired(self) -> bool:
        """Check if certificate is expired."""
        if self.valid_until:
            return datetime.utcnow() > self.valid_until
        return False

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "https_available": self.https_available,
            "is_valid": self.is_valid,
            "issuer": self.issuer,
            "subject": self.subject,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "serial_number": self.serial_number,
            "fingerprint": self.fingerprint,
            "alt_names": self.alt_names,
            "days_until_expiry": self.days_until_expiry,
            "is_expired": self.is_expired,
            "error": self.error,
        }


class SSLVerifier:
    """SSL certificate verification."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    def verify(self, domain: str) -> SSLVerificationResult:
        """Verify SSL certificate for a domain."""
        domain = self._clean_domain(domain)

        # Check if HTTPS is available
        https_available = self._check_https_available(domain)

        if not https_available:
            return SSLVerificationResult(
                domain=domain,
                https_available=False,
                error="HTTPS not available on this domain",
            )

        # Get certificate details
        try:
            return self._get_certificate_details(domain)
        except Exception as e:
            logger.error(f"SSL verification failed for {domain}: {e}")
            return SSLVerificationResult(
                domain=domain,
                https_available=True,
                is_valid=False,
                error=f"Certificate verification failed: {str(e)}",
            )

    def _clean_domain(self, domain: str) -> str:
        """Clean domain string."""
        domain = domain.lower().strip()

        # Remove protocol
        if domain.startswith("http://"):
            domain = domain[7:]
        elif domain.startswith("https://"):
            domain = domain[8:]

        # Remove path
        domain = domain.split("/")[0]
        domain = domain.split(":")[0]

        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    def _check_https_available(self, domain: str) -> bool:
        """Check if HTTPS is available."""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, 443), timeout=10):
                return True
        except Exception:
            return False

    def _get_certificate_details(self, domain: str) -> SSLVerificationResult:
        """Get detailed certificate information."""
        context = ssl.create_default_context()

        with socket.create_connection((domain, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=domain) as ssock:
                cert = ssock.getpeercert()
                cipher = ssock.cipher()
                version = ssock.version()

                if not cert:
                    return SSLVerificationResult(
                        domain=domain,
                        https_available=True,
                        is_valid=False,
                        error="No certificate found",
                    )

                # Extract issuer
                issuer_parts = cert.get("issuer", ())
                issuer = self._parse_dn(issuer_parts)

                # Extract subject
                subject_parts = cert.get("subject", ())
                subject = self._parse_dn(subject_parts)

                # Parse dates
                not_before = cert.get("notBefore")
                not_after = cert.get("notAfter")

                valid_from = self._parse_ssl_date(not_before) if not_before else None
                valid_until = self._parse_ssl_date(not_after) if not_after else None

                # Get serial number
                serial = cert.get("serialNumber")

                # Get SANs (Subject Alternative Names)
                san = cert.get("subjectAltName", ())
                alt_names = [name[1] for name in san if name[0] == "DNS"]

                # Check validity
                is_valid = self._is_certificate_valid(cert)

                return SSLVerificationResult(
                    domain=domain,
                    https_available=True,
                    is_valid=is_valid,
                    issuer=issuer,
                    subject=subject,
                    valid_from=valid_from,
                    valid_until=valid_until,
                    serial_number=serial,
                    alt_names=alt_names,
                )

    def _parse_dn(self, dn_parts) -> str:
        """Parse a distinguished name into a string.

        ``ssl.getpeercert()`` returns issuer/subject as a tuple of RDNs, where
        each RDN is itself a tuple of ``(key, value)`` pairs, e.g.::

            ((('countryName', 'US'),), (('organizationName', 'DigiCert Inc'),))

        The previous implementation indexed ``part[1]`` on the RDN wrapper
        (a 1-element tuple), raising "tuple index out of range".
        """
        if not dn_parts:
            return ""

        parts = []
        for rdn in dn_parts:
            if not isinstance(rdn, (tuple, list)):
                continue
            for attr in rdn:
                if isinstance(attr, (tuple, list)) and len(attr) >= 2:
                    parts.append(f"{attr[0]}={attr[1]}")

        return ", ".join(parts)

    def _parse_ssl_date(self, date_str: str) -> Optional[datetime]:
        """Parse SSL certificate date string."""
        # SSL dates are typically in format: 'Jan 15 12:00:00 2024 GMT'
        try:
            return datetime.strptime(date_str, "%b %d %H:%M:%S %Y %Z")
        except ValueError:
            try:
                return datetime.strptime(date_str.replace(" GMT", ""), "%b %d %H:%M:%S %Y")
            except ValueError:
                return None

    def _is_certificate_valid(self, cert: Dict) -> bool:
        """Check if certificate is currently valid."""
        try:
            not_before = cert.get("notBefore")
            not_after = cert.get("notAfter")

            if not not_before or not not_after:
                return False

            valid_from = self._parse_ssl_date(not_before)
            valid_until = self._parse_ssl_date(not_after)

            if not valid_from or not valid_until:
                return False

            now = datetime.utcnow()
            return valid_from <= now <= valid_until
        except Exception:
            return False


# Singleton instance
ssl_verifier = SSLVerifier()
