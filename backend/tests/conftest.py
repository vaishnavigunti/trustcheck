"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def sample_domain():
    """Sample domain for testing."""
    return "google.com"


@pytest.fixture
def sample_email():
    """Sample email for testing."""
    return "test@example.com"
