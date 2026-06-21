"""Unit tests for security guards (SSRF protection)."""

import pytest

from app.core.ssrf import SSRFError, is_public_url, validate_public_url


class TestSSRFGuard:
    """The verification engine fetches user-supplied URLs server-side; the
    SSRF guard must block anything that is not a public, routable http(s) URL."""

    @pytest.mark.parametrize(
        "url",
        [
            "http://localhost:8000/admin",
            "http://127.0.0.1/",
            "http://169.254.169.254/latest/meta-data/",  # cloud metadata
            "http://10.0.0.5/",
            "http://192.168.1.1/",
            "http://172.16.0.1/",
            "http://[::1]/",
            "https://metadata.google.internal/",
            "file:///etc/passwd",
            "ftp://example.com/",
            "gopher://example.com/",
            "",
        ],
    )
    def test_blocks_non_public_targets(self, url):
        assert is_public_url(url) is False
        with pytest.raises(SSRFError):
            validate_public_url(url)

    @pytest.mark.parametrize(
        "url",
        [
            "https://example.com/",
            "https://www.google.com/careers",
            "http://example.com",
        ],
    )
    def test_allows_public_targets(self, url):
        assert is_public_url(url) is True
        # Returns the (stripped) URL unchanged for valid public targets.
        assert validate_public_url(url) == url
