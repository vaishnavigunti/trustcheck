"""Website analysis module."""

import time
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from app.core import get_logger, get_settings
from app.core.config import Settings
from app.core.ssrf import SSRFError, guarded_request, validate_public_url

logger = get_logger(__name__)


class WebsiteAnalysisResult:
    """Result of website analysis."""

    def __init__(
        self,
        url: str,
        accessible: bool,
        status_code: Optional[int] = None,
        title: Optional[str] = None,
        has_about_page: bool = False,
        has_contact_page: bool = False,
        has_privacy_policy: bool = False,
        has_terms_page: bool = False,
        social_links: Optional[List[str]] = None,
        emails_found: Optional[List[str]] = None,
        phones_found: Optional[List[str]] = None,
        response_time_ms: Optional[int] = None,
        error: Optional[str] = None,
    ):
        self.url = url
        self.accessible = accessible
        self.status_code = status_code
        self.title = title
        self.has_about_page = has_about_page
        self.has_contact_page = has_contact_page
        self.has_privacy_policy = has_privacy_policy
        self.has_terms_page = has_terms_page
        self.social_links = social_links or []
        self.emails_found = emails_found or []
        self.phones_found = phones_found or []
        self.response_time_ms = response_time_ms
        self.error = error

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "accessible": self.accessible,
            "status_code": self.status_code,
            "title": self.title,
            "has_about_page": self.has_about_page,
            "has_contact_page": self.has_contact_page,
            "has_privacy_policy": self.has_privacy_policy,
            "has_terms_page": self.has_terms_page,
            "social_links": self.social_links,
            "emails_found": self.emails_found,
            "phones_found": self.phones_found,
            "response_time_ms": self.response_time_ms,
            "error": self.error,
        }


class WebsiteAnalyzer:
    """Website content analyzer."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })

    def analyze(self, url: str) -> WebsiteAnalysisResult:
        """Analyze a website."""
        url = self._normalize_url(url)

        # SSRF guard: refuse to fetch internal / non-public targets.
        try:
            url = validate_public_url(url)
        except SSRFError as e:
            logger.warning(f"Website analysis blocked for {url}: {e}")
            return WebsiteAnalysisResult(
                url=url,
                accessible=False,
                error="URL is not a publicly reachable address",
            )

        try:
            start_time = time.time()
            response = guarded_request(
                self.session,
                "GET",
                url,
                timeout=self.settings.request_timeout_seconds,
            )
            response_time_ms = int((time.time() - start_time) * 1000)

            if response.status_code != 200:
                return WebsiteAnalysisResult(
                    url=url,
                    accessible=False,
                    status_code=response.status_code,
                    response_time_ms=response_time_ms,
                    error=f"HTTP {response.status_code}",
                )

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract title
            title = self._extract_title(soup)

            # Check for important pages
            about_exists = self._check_page_exists(url, ["/about", "/about-us", "/company"])
            contact_exists = self._check_page_exists(url, ["/contact", "/contact-us", "/support"])
            privacy_exists = self._check_page_exists(url, ["/privacy", "/privacy-policy"])
            terms_exists = self._check_page_exists(url, ["/terms", "/terms-of-service", "/tos"])

            # Extract social links from homepage
            social_links = self._extract_social_links(soup, url)

            # Extract contact info
            emails, phones = self._extract_contact_info(soup)

            return WebsiteAnalysisResult(
                url=url,
                accessible=True,
                status_code=response.status_code,
                title=title,
                has_about_page=about_exists,
                has_contact_page=contact_exists,
                has_privacy_policy=privacy_exists,
                has_terms_page=terms_exists,
                social_links=social_links,
                emails_found=emails,
                phones_found=phones,
                response_time_ms=response_time_ms,
            )

        except requests.exceptions.Timeout:
            return WebsiteAnalysisResult(
                url=url,
                accessible=False,
                error="Request timed out",
            )
        except requests.exceptions.ConnectionError:
            return WebsiteAnalysisResult(
                url=url,
                accessible=False,
                error="Connection error",
            )
        except Exception as e:
            logger.error(f"Website analysis failed for {url}: {e}")
            return WebsiteAnalysisResult(
                url=url,
                accessible=False,
                error=f"Analysis failed: {str(e)}",
            )

    def _normalize_url(self, url: str) -> str:
        """Normalize URL to absolute URL with https."""
        url = url.strip()

        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"

        return url

    def _extract_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract page title."""
        title_tag = soup.find("title")
        if title_tag:
            return title_tag.get_text(strip=True)
        return None

    def _check_page_exists(self, base_url: str, paths: List[str]) -> bool:
        """Check if a page exists at common paths."""
        for path in paths:
            try:
                full_url = urljoin(base_url, path)
                response = guarded_request(
                    self.session,
                    "HEAD",
                    full_url,
                    timeout=5,
                )
                if response.status_code == 200:
                    return True
            except Exception:
                continue
        return False

    def _extract_social_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract social media links from page."""
        social_patterns = [
            "facebook.com", "twitter.com", "x.com", "linkedin.com",
            "instagram.com", "youtube.com", "github.com", "gitlab.com"
        ]

        links = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if any(pattern in href.lower() for pattern in social_patterns):
                # Normalize URL
                if href.startswith("//"):
                    href = f"https:{href}"
                elif href.startswith("/"):
                    href = urljoin(base_url, href)

                links.append(href)

        # Remove duplicates while preserving order
        seen = set()
        unique_links = []
        for link in links:
            if link not in seen:
                seen.add(link)
                unique_links.append(link)

        return unique_links[:10]  # Limit to first 10

    def _extract_contact_info(self, soup: BeautifulSoup) -> tuple[List[str], List[str]]:
        """Extract emails and phone numbers from page."""
        import re

        text = soup.get_text()

        # Simple email regex
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = list(set(re.findall(email_pattern, text)))

        # Simple phone regex (matches various formats)
        phone_pattern = r'[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}'
        phones = list(set(re.findall(phone_pattern, text)))

        return emails[:5], phones[:5]  # Limit results


# Singleton instance
website_analyzer = WebsiteAnalyzer()
