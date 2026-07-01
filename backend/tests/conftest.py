"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Create a test client.

    Used as a context manager so the internal anyio portal (which hosts the
    async event loop for the ASGI app) is properly started and stopped within
    the fixture lifecycle.  Without this, pytest-asyncio's function-scoped loop
    gets closed while the portal thread still references it, producing
    "RuntimeError: Event loop is closed" in subsequent sync tests.
    """
    with TestClient(app) as c:
        yield c


@pytest.fixture
def sample_domain():
    """Sample domain for testing."""
    return "google.com"


@pytest.fixture
def sample_email():
    """Sample email for testing."""
    return "test@example.com"
