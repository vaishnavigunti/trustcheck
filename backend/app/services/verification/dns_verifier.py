"""DNS verification module."""

import socket
from typing import Dict, List, Optional

import dns.resolver
import dns.exception

from app.core import get_logger, get_settings
from app.core.config import Settings

logger = get_logger(__name__)


class DNSVerificationResult:
    """Result of DNS verification."""

    def __init__(
        self,
        domain: str,
        has_mx_records: bool,
        mx_records: Optional[List[Dict]] = None,
        has_spf: bool = False,
        spf_record: Optional[str] = None,
        has_dkim: bool = False,
        dkim_records: Optional[List[str]] = None,
        has_dmarc: bool = False,
        dmarc_record: Optional[str] = None,
        nameservers: Optional[List[str]] = None,
        error: Optional[str] = None,
    ):
        self.domain = domain
        self.has_mx_records = has_mx_records
        self.mx_records = mx_records or []
        self.has_spf = has_spf
        self.spf_record = spf_record
        self.has_dkim = has_dkim
        self.dkim_records = dkim_records or []
        self.has_dmarc = has_dmarc
        self.dmarc_record = dmarc_record
        self.nameservers = nameservers or []
        self.error = error

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "domain": self.domain,
            "has_mx_records": self.has_mx_records,
            "mx_records": self.mx_records,
            "has_spf": self.has_spf,
            "spf_record": self.spf_record,
            "has_dkim": self.has_dkim,
            "dkim_records": self.dkim_records,
            "has_dmarc": self.has_dmarc,
            "dmarc_record": self.dmarc_record,
            "nameservers": self.nameservers,
            "error": self.error,
        }


class DNSVerifier:
    """DNS record verification."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    def verify(self, domain: str) -> DNSVerificationResult:
        """Verify DNS records for a domain."""
        domain = self._clean_domain(domain)

        try:
            # Check MX records
            mx_records = self._get_mx_records(domain)
            has_mx = len(mx_records) > 0

            # Check SPF
            has_spf, spf_record = self._get_spf_record(domain)

            # Check DKIM (common selectors)
            has_dkim, dkim_records = self._get_dkim_records(domain)

            # Check DMARC
            has_dmarc, dmarc_record = self._get_dmarc_record(domain)

            # Get nameservers
            nameservers = self._get_nameservers(domain)

            return DNSVerificationResult(
                domain=domain,
                has_mx_records=has_mx,
                mx_records=mx_records,
                has_spf=has_spf,
                spf_record=spf_record,
                has_dkim=has_dkim,
                dkim_records=dkim_records,
                has_dmarc=has_dmarc,
                dmarc_record=dmarc_record,
                nameservers=nameservers,
            )

        except Exception as e:
            logger.error(f"DNS verification failed for {domain}: {e}")
            return DNSVerificationResult(
                domain=domain,
                has_mx_records=False,
                error=f"DNS lookup failed: {str(e)}",
            )

    def verify_email_domain(self, email: str) -> DNSVerificationResult:
        """Verify DNS records for an email domain."""
        # Extract domain from email
        domain = email.split("@")[-1].lower().strip()
        return self.verify(domain)

    def _clean_domain(self, domain: str) -> str:
        """Clean domain string."""
        domain = domain.lower().strip()

        if domain.startswith("http://"):
            domain = domain[7:]
        elif domain.startswith("https://"):
            domain = domain[8:]

        domain = domain.split("/")[0]
        domain = domain.split(":")[0]

        if domain.startswith("www."):
            domain = domain[4:]

        return domain

    def _get_mx_records(self, domain: str) -> List[Dict]:
        """Get MX records for a domain."""
        try:
            answers = dns.resolver.resolve(domain, "MX")
            records = []
            for rdata in answers:
                records.append({
                    "priority": rdata.preference,
                    "server": str(rdata.exchange).rstrip("."),
                })
            return records
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
            return []
        except Exception as e:
            logger.warning(f"MX lookup failed for {domain}: {e}")
            return []

    def _get_spf_record(self, domain: str) -> tuple[bool, Optional[str]]:
        """Get SPF record for a domain."""
        try:
            answers = dns.resolver.resolve(domain, "TXT")
            for rdata in answers:
                for txt_string in rdata.strings:
                    txt = txt_string.decode() if isinstance(txt_string, bytes) else txt_string
                    if txt.startswith("v=spf1"):
                        return True, txt
            return False, None
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
            return False, None
        except Exception as e:
            logger.warning(f"SPF lookup failed for {domain}: {e}")
            return False, None

    def _get_dkim_records(self, domain: str) -> tuple[bool, List[str]]:
        """Get DKIM records for common selectors."""
        common_selectors = ["default", "google", "selector1", "selector2", "dkim", "mail"]
        records = []

        for selector in common_selectors:
            try:
                dkim_domain = f"{selector}._domainkey.{domain}"
                answers = dns.resolver.resolve(dkim_domain, "TXT")
                for rdata in answers:
                    for txt_string in rdata.strings:
                        txt = txt_string.decode() if isinstance(txt_string, bytes) else txt_string
                        if "DKIM" in txt or txt.startswith("v=DKIM"):
                            records.append(txt)
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
                continue
            except Exception:
                continue

        return len(records) > 0, records

    def _get_dmarc_record(self, domain: str) -> tuple[bool, Optional[str]]:
        """Get DMARC record for a domain."""
        try:
            dmarc_domain = f"_dmarc.{domain}"
            answers = dns.resolver.resolve(dmarc_domain, "TXT")
            for rdata in answers:
                for txt_string in rdata.strings:
                    txt = txt_string.decode() if isinstance(txt_string, bytes) else txt_string
                    if txt.startswith("v=DMARC1"):
                        return True, txt
            return False, None
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
            return False, None
        except Exception as e:
            logger.warning(f"DMARC lookup failed for {domain}: {e}")
            return False, None

    def _get_nameservers(self, domain: str) -> List[str]:
        """Get nameservers for a domain."""
        try:
            answers = dns.resolver.resolve(domain, "NS")
            return [str(rdata).rstrip(".") for rdata in answers]
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.exception.Timeout):
            return []
        except Exception as e:
            logger.warning(f"NS lookup failed for {domain}: {e}")
            return []


# Singleton instance
dns_verifier = DNSVerifier()
