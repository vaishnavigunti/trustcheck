"""Domain verification module."""

import socket
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import whois
from whois import WhoisEntry

from app.core import get_logger, get_settings
from app.core.config import Settings

logger = get_logger(__name__)


class DomainVerificationResult:
    """Result of domain verification."""

    def __init__(
        self,
        domain: str,
        exists: bool,
        registration_date: Optional[datetime] = None,
        expiration_date: Optional[datetime] = None,
        registrar: Optional[str] = None,
        name_servers: Optional[List[str]] = None,
        error: Optional[str] = None,
    ):
        self.domain = domain
        self.exists = exists
        self.registration_date = registration_date
        self.expiration_date = expiration_date
        self.registrar = registrar
        self.name_servers = name_servers or []
        self.error = error

    @property
    def domain_age_days(self) -> Optional[int]:
        """Calculate domain age in days."""
        if self.registration_date:
            return (datetime.utcnow() - self.registration_date).days
        return None

    @property
    def days_until_expiration(self) -> Optional[int]:
        """Calculate days until domain expires."""
        if self.expiration_date:
            return (self.expiration_date - datetime.utcnow()).days
        return None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "exists": self.exists,
            "registration_date": self.registration_date.isoformat() if self.registration_date else None,
            "expiration_date": self.expiration_date.isoformat() if self.expiration_date else None,
            "registrar": self.registrar,
            "name_servers": self.name_servers,
            "domain_age_days": self.domain_age_days,
            "days_until_expiration": self.days_until_expiration,
            "error": self.error,
        }


class DomainVerifier:
    """Domain verification using WHOIS data."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    def verify(self, domain: str) -> DomainVerificationResult:
        """Verify domain existence and registration details."""
        # Clean domain (remove protocol if present)
        domain = self._clean_domain(domain)

        # First check if domain resolves
        exists = self._check_domain_exists(domain)

        if not exists:
            logger.warning(f"Domain does not resolve: {domain}")
            return DomainVerificationResult(
                domain=domain,
                exists=False,
                error="Domain does not resolve to an IP address",
            )

        # Get WHOIS data
        try:
            whois_data = whois.whois(domain)
            return self._parse_whois_data(domain, whois_data)
        except Exception as e:
            logger.error(f"WHOIS lookup failed for {domain}: {e}")
            # Return partial result - domain exists but WHOIS failed
            return DomainVerificationResult(
                domain=domain,
                exists=True,
                error=f"WHOIS lookup failed: {str(e)}",
            )

    def _clean_domain(self, domain: str) -> str:
        """Clean domain string (remove protocol, path, etc.)."""
        domain = domain.lower().strip()

        # Remove protocol
        if domain.startswith("http://"):
            domain = domain[7:]
        elif domain.startswith("https://"):
            domain = domain[8:]

        # Remove path, query params
        domain = domain.split("/")[0]
        domain = domain.split(":")[0]  # Remove port

        # Remove www. prefix
        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    def _check_domain_exists(self, domain: str) -> bool:
        """Check if domain resolves to an IP address."""
        try:
            socket.gethostbyname(domain)
            return True
        except socket.gaierror:
            return False

    def _parse_whois_data(
        self,
        domain: str,
        whois_data: WhoisEntry,
    ) -> DomainVerificationResult:
        """Parse WHOIS data into structured result."""
        # Extract dates - handle different formats
        registration_date = self._parse_date(whois_data.creation_date)
        expiration_date = self._parse_date(whois_data.expiration_date)

        # Extract registrar
        registrar = whois_data.registrar
        if isinstance(registrar, list):
            registrar = registrar[0]

        # Extract name servers
        name_servers = whois_data.name_servers
        if name_servers:
            if isinstance(name_servers, str):
                name_servers = [name_servers]
            name_servers = [ns.lower() for ns in name_servers]

        return DomainVerificationResult(
            domain=domain,
            exists=True,
            registration_date=registration_date,
            expiration_date=expiration_date,
            registrar=registrar,
            name_servers=name_servers,
        )

    def _parse_date(self, date_value) -> Optional[datetime]:
        """Parse various date formats from WHOIS."""
        if date_value is None:
            return None

        if isinstance(date_value, datetime):
            return date_value

        if isinstance(date_value, list) and len(date_value) > 0:
            date_value = date_value[0]
            if isinstance(date_value, datetime):
                return date_value

        # Try parsing string dates
        if isinstance(date_value, str):
            formats = [
                "%Y-%m-%d",
                "%Y-%m-%d %H:%M:%S",
                "%d-%b-%Y",
                "%d-%b-%Y %H:%M:%S",
                "%d.%m.%Y",
                "%Y%m%d",
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(date_value, fmt)
                except ValueError:
                    continue

        return None


# Singleton instance
domain_verifier = DomainVerifier()
