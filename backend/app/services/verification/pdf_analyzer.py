"""PDF offer letter analysis module."""

import re
from typing import Dict, List, Optional

import fitz  # PyMuPDF
import pdfplumber

from app.core import get_logger, get_settings
from app.core.config import Settings

logger = get_logger(__name__)


class PDFAnalysisResult:
    """Result of PDF analysis."""

    def __init__(
        self,
        file_path: str,
        success: bool,
        raw_text: Optional[str] = None,
        company_name: Optional[str] = None,
        email: Optional[str] = None,
        website: Optional[str] = None,
        address: Optional[str] = None,
        phone: Optional[str] = None,
        position: Optional[str] = None,
        salary: Optional[str] = None,
        start_date: Optional[str] = None,
        other_entities: Optional[Dict] = None,
        errors: Optional[List[str]] = None,
        page_count: int = 0,
    ):
        self.file_path = file_path
        self.success = success
        self.raw_text = raw_text
        self.company_name = company_name
        self.email = email
        self.website = website
        self.address = address
        self.phone = phone
        self.position = position
        self.salary = salary
        self.start_date = start_date
        self.other_entities = other_entities or {}
        self.errors = errors or []
        self.page_count = page_count

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "file_path": self.file_path,
            "success": self.success,
            "company_name": self.company_name,
            "email": self.email,
            "website": self.website,
            "address": self.address,
            "phone": self.phone,
            "position": self.position,
            "salary": self.salary,
            "start_date": self.start_date,
            "other_entities": self.other_entities,
            "page_count": self.page_count,
            "errors": self.errors,
        }


class PDFAnalyzer:
    """PDF offer letter text extraction and analysis."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()

    def analyze(self, file_path: str) -> PDFAnalysisResult:
        """Analyze a PDF offer letter."""
        try:
            # Extract text using PyMuPDF first
            text = self._extract_text_fitz(file_path)

            if not text or len(text.strip()) < 50:
                # Fallback to pdfplumber for complex layouts
                text = self._extract_text_plumber(file_path)

            if not text:
                return PDFAnalysisResult(
                    file_path=file_path,
                    success=False,
                    errors=["Could not extract text from PDF"],
                )

            # Get page count
            page_count = self._get_page_count(file_path)

            # Extract structured data
            result = self._extract_structured_data(text)
            result.file_path = file_path
            result.success = True
            result.page_count = page_count
            result.raw_text = text[:5000]  # Store first 5000 chars

            return result

        except Exception as e:
            logger.error(f"PDF analysis failed for {file_path}: {e}")
            return PDFAnalysisResult(
                file_path=file_path,
                success=False,
                errors=[f"Analysis failed: {str(e)}"],
            )

    def _extract_text_fitz(self, file_path: str) -> Optional[str]:
        """Extract text using PyMuPDF."""
        try:
            doc = fitz.open(file_path)
            text = ""
            for page in doc:
                text += page.get_text()
            doc.close()
            return text
        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed: {e}")
            return None

    def _extract_text_plumber(self, file_path: str) -> Optional[str]:
        """Extract text using pdfplumber."""
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            logger.warning(f"pdfplumber extraction failed: {e}")
            return None

    def _get_page_count(self, file_path: str) -> int:
        """Get number of pages in PDF."""
        try:
            doc = fitz.open(file_path)
            count = doc.page_count
            doc.close()
            return count
        except Exception:
            return 0

    def _extract_structured_data(self, text: str) -> PDFAnalysisResult:
        """Extract structured data from text."""
        result = PDFAnalysisResult(
            file_path="",
            success=True,
        )

        # Extract email
        result.email = self._extract_email(text)

        # Extract website
        result.website = self._extract_website(text)

        # Extract phone
        result.phone = self._extract_phone(text)

        # Extract company name (heuristic approach)
        result.company_name = self._extract_company_name(text)

        # Extract address
        result.address = self._extract_address(text)

        # Extract position
        result.position = self._extract_position(text)

        # Extract salary
        result.salary = self._extract_salary(text)

        # Extract start date
        result.start_date = self._extract_start_date(text)

        return result

    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address."""
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(pattern, text)
        # Filter out common false positives
        filtered = [m for m in matches if not any(x in m.lower() for x in ['example.com', 'domain.com'])]
        return filtered[0] if filtered else None

    def _extract_website(self, text: str) -> Optional[str]:
        """Extract website URL."""
        pattern = r'https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:[\w.])*)?)?'
        matches = re.findall(pattern, text)
        if matches:
            return matches[0]

        # Try domain pattern
        pattern = r'(?:www\.)?([a-zA-Z0-9-]+\.[a-zA-Z]{2,})(?:/[^\s]*)?'
        matches = re.findall(pattern, text)
        if matches:
            return f"https://{matches[0]}"

        return None

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number."""
        # Various phone formats
        patterns = [
            r'\+?[1-9]\d{1,2}[\s.-]?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}',
            r'\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}',
            r'\+\d{2}[\s.-]?\d{10}',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                return matches[0]
        return None

    # Company legal suffixes (US + a few international forms).
    # Ordered longest-first so e.g. "Corporation" wins over "Corp" and the
    # full suffix is captured rather than truncated.
    _COMPANY_SUFFIX = (
        r'(?:Incorporated|Corporation|Limited|Company|'
        r'Pvt\.?\s*Ltd\.?|Pte\.?\s*Ltd\.?|L\.L\.C\.|LLC|PLC|GmbH|'
        r'Inc\.?|Corp\.?|Ltd\.?|Co\.|AG|S\.?A\.?|N\.?V\.?)'
    )
    # A company name is a short run of Title-Case tokens (with a few lowercase
    # connectors) on a SINGLE line. Building it from capitalised tokens — rather
    # than a broad char class — stops it from swallowing surrounding sentence
    # text (the old `\s`-based pattern grabbed whole lines).
    _NAME_WORD = r'[A-Z][A-Za-z0-9&.\-]*'
    _NAME_CONNECTOR = r'(?:and|of|the|for|&)'
    _COMPANY_CORE = rf'{_NAME_WORD}(?:[ ,]+(?:{_NAME_WORD}|{_NAME_CONNECTOR})){{0,5}}'

    def _clean_company(self, value: str) -> str:
        """Normalise whitespace and trim stray separators (keeps trailing '.')."""
        value = re.sub(r'[ \t]+', ' ', value).strip(' \t\n,-')
        return value

    def _extract_company_name(self, text: str) -> Optional[str]:
        """Extract company name using heuristics (most specific first)."""
        # 1) A name explicitly carrying a legal suffix (e.g. "Stripe, Inc.").
        #    This is the strongest signal and usually sits in the letterhead.
        m = re.search(rf'\b({self._COMPANY_CORE}[\s,]+{self._COMPANY_SUFFIX})', text)
        if m:
            return self._clean_company(m.group(1))

        # 2) Contextual phrasing. The keyword is case-insensitive (scoped inline
        #    flag) but the captured name stays Title-Case, so it can't run on
        #    into the rest of the sentence.
        context_patterns = [
            rf'(?i:\b(?:join|joining|with|from|employer|company))\s*:?\s+({self._COMPANY_CORE})',
            rf'(?i:\bat)\s+({self._COMPANY_CORE})',
        ]
        for pattern in context_patterns:
            m = re.search(pattern, text)
            if m:
                cleaned = self._clean_company(m.group(1))
                if len(cleaned) >= 2:
                    return cleaned

        # 3) Fallback: first short, header-like line near the top.
        skip = ('offer', 'letter', 'employment', 'date', 'dear', 'sincerely',
                're:', 'subject', 'to whom')
        for line in text.split('\n')[:8]:
            line = line.strip()
            if 2 < len(line) <= 60 and not any(x in line.lower() for x in skip):
                return self._clean_company(line)

        return None

    def _extract_address(self, text: str) -> Optional[str]:
        """Extract address."""
        # Look for address patterns
        pattern = r'\d+\s+[A-Za-z0-9\s.,]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Way|Court|Ct|Plaza|Parkway|Pkwy)\s*,?\s*(?:[A-Za-z\s]+,?\s*)?(?:[A-Z]{2})?\s*\d{5}(?:-\d{4})?'
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            return matches[0]

        # Look for simpler patterns
        pattern = r'\d+\s+[A-Za-z0-9\s]+(?:\s*,\s*[A-Za-z]+,?\s*[A-Z]{2}\s*\d{5})?'
        matches = re.findall(pattern, text)
        if matches:
            return matches[0]

        return None

    def _extract_position(self, text: str) -> Optional[str]:
        """Extract job position."""
        patterns = [
            r'position\s+(?:of\s+)?["\']?([^"\']+)["\']?(?:\s+at|\s+with)',
            r'(?:as|for)\s+(?:a|an)\s+([A-Za-z\s]+(?:Engineer|Developer|Manager|Analyst|Designer|Consultant|Specialist|Coordinator))',
            r'(?:role|title)\s*:?\s*["\']?([^"\']+)["\']?',
            r'\b([A-Z][a-z]+\s+(?:Engineer|Developer|Manager|Analyst|Designer|Consultant|Specialist|Coordinator|Intern))\b',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0].strip()

        return None

    def _extract_salary(self, text: str) -> Optional[str]:
        """Extract salary information."""
        patterns = [
            r'(?:salary|compensation|pay)\s*:?\s*[$₹€£]?\s*([\d,]+(?:\.\d{2})?)',
            r'[$₹€£]?\s*([\d,]+(?:\.\d{2})?)\s*(?:per|/)\s*(?:year|annum|month|hour)',
            r'annual\s+(?:salary|compensation)\s*:?\s*[$₹€£]?\s*([\d,]+(?:K)?)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]

        return None

    def _extract_start_date(self, text: str) -> Optional[str]:
        """Extract start date."""
        patterns = [
            r'(?:start|commenc|joining)\s+(?:date|on)\s*:?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'(?:effective|beginning)\s+(?:date|on)\s*:?\s*([A-Za-z]+\s+\d{1,2},?\s+\d{4})',
            r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
            r'\b(\d{4}[/-]\d{1,2}[/-]\d{1,2})\b',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0]

        return None


# Singleton instance
pdf_analyzer = PDFAnalyzer()
