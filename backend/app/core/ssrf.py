"""SSRF (Server-Side Request Forgery) protection.

The verification engine fetches user-supplied URLs server-side (website
analysis, page-existence checks). Without guarding, a user could point a
``target_url`` at internal infrastructure — ``http://localhost``, private
RFC1918 ranges, or the cloud metadata endpoint ``169.254.169.254`` — and use
our server as a proxy to reach it. This module validates that a URL resolves
only to public, routable IP addresses and provides a redirect-following HTTP
helper that re-validates every hop.
"""

import ipaddress
import socket
from typing import List
from urllib.parse import urlparse

import requests

from app.core.logging import get_logger

logger = get_logger(__name__)

# Schemes we are willing to request server-side.
_ALLOWED_SCHEMES = {"http", "https"}

# Hostnames that must never be resolved/fetched, regardless of DNS.
_BLOCKED_HOSTNAMES = {
    "localhost",
    "metadata.google.internal",  # GCP metadata
}


class SSRFError(ValueError):
    """Raised when a URL targets a non-public / disallowed address."""


def _is_public_ip(ip_str: str) -> bool:
    """Return True only for globally routable, non-internal IP addresses."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return False

    # Reject loopback, private (RFC1918), link-local (incl. 169.254.169.254
    # cloud metadata), multicast, reserved, unspecified, and CGNAT-style ranges.
    if (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        return False

    # Explicitly block the IPv6 unique-local range (fc00::/7) which is_private
    # already covers, plus IPv4-mapped IPv6 that could smuggle a private v4.
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        return _is_public_ip(str(ip.ipv4_mapped))

    return True


def _resolve_host(host: str) -> List[str]:
    """Resolve a hostname to all of its IP addresses (v4 and v6)."""
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror as exc:
        raise SSRFError(f"Could not resolve host: {host}") from exc
    return list({info[4][0] for info in infos})


def validate_public_url(url: str) -> str:
    """Validate that ``url`` is an http(s) URL resolving only to public IPs.

    Returns the (stripped) URL on success; raises :class:`SSRFError` otherwise.
    """
    if not url or not isinstance(url, str):
        raise SSRFError("A URL is required")

    url = url.strip()
    parsed = urlparse(url)

    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        raise SSRFError("Only http and https URLs are allowed")

    host = parsed.hostname
    if not host:
        raise SSRFError("URL is missing a host")

    if host.lower() in _BLOCKED_HOSTNAMES:
        raise SSRFError("Target host is not allowed")

    # If the host is a literal IP, validate it directly; otherwise resolve.
    try:
        ipaddress.ip_address(host)
        candidates = [host]
    except ValueError:
        candidates = _resolve_host(host)

    if not candidates:
        raise SSRFError(f"Could not resolve host: {host}")

    for ip in candidates:
        if not _is_public_ip(ip):
            logger.warning("Blocked SSRF attempt", url=url, resolved_ip=ip)
            raise SSRFError("Target resolves to a non-public address")

    return url


def is_public_url(url: str) -> bool:
    """Non-raising variant of :func:`validate_public_url`."""
    try:
        validate_public_url(url)
        return True
    except SSRFError:
        return False


def guarded_request(
    session: requests.Session,
    method: str,
    url: str,
    *,
    timeout: int,
    max_redirects: int = 3,
    **kwargs,
) -> requests.Response:
    """Perform an HTTP request, validating the host of every redirect hop.

    ``requests``' built-in redirect handling would follow a public URL that
    302-redirects to ``http://169.254.169.254`` — so we disable automatic
    redirects and follow them manually, re-validating each ``Location``.
    """
    kwargs.pop("allow_redirects", None)
    current_url = validate_public_url(url)

    for _ in range(max_redirects + 1):
        response = session.request(
            method,
            current_url,
            timeout=timeout,
            allow_redirects=False,
            **kwargs,
        )

        if response.is_redirect or response.is_permanent_redirect:
            location = response.headers.get("Location")
            if not location:
                return response
            # Resolve relative redirects against the current URL.
            current_url = validate_public_url(requests.compat.urljoin(current_url, location))
            continue

        return response

    raise SSRFError("Too many redirects")
