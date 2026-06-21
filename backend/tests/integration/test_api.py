"""Integration tests for API endpoints."""

import uuid

import pytest


def _unique_email() -> str:
    return f"test_{uuid.uuid4().hex[:10]}@example.com"


def test_health_check(client):
    """Test health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "name" in response.json()


def test_auth_endpoints_require_authentication(client):
    """Test that auth endpoints return 401 without token."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_cors_headers_present(client):
    """Test CORS headers are present."""
    response = client.options("/", headers={
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
    })
    assert "access-control-allow-origin" in response.headers


def test_security_headers_present(client):
    """Test security headers are present."""
    response = client.get("/")
    assert "x-frame-options" in response.headers
    assert "x-content-type-options" in response.headers
    assert "x-xss-protection" in response.headers


def test_register_then_refresh(client):
    """A newly registered user must be able to refresh their token immediately.

    Regression: register() previously never persisted the refresh-token hash,
    so /auth/refresh rejected the freshly issued token.
    """
    email = _unique_email()
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Str0ngPass!23", "full_name": "Reg Test"},
    )
    assert reg.status_code == 201, reg.text
    refresh_token = reg.json()["tokens"]["refresh_token"]

    refreshed = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refreshed.status_code == 200, refreshed.text
    assert refreshed.json()["access_token"]


def test_token_rotation_revokes_old_refresh_token(client):
    """Refreshing rotates the refresh token and revokes the old one.

    Regression: tokens minted in the same second were byte-identical and
    collided on the unique token_hash; each issuance now carries a jti.
    """
    email = _unique_email()
    client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Str0ngPass!23", "full_name": "Rot Test"},
    )
    login = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "Str0ngPass!23"}
    )
    assert login.status_code == 200, login.text
    old_refresh = login.json()["tokens"]["refresh_token"]

    first = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert first.status_code == 200, first.text

    # Reusing the now-rotated token must fail.
    reuse = client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert reuse.status_code == 401, reuse.text


async def test_report_generation_is_serializable():
    """Generating a report returns a fully-loaded, serializable Report.

    Regression: server-default timestamps (created_at/updated_at) were not
    loaded after flush, so serializing the response raised MissingGreenlet
    (a lazy DB load attempted in a sync context).
    """
    from app.core.database import AsyncSessionLocal
    from app.core.security import get_password_hash
    from app.models.user import User
    from app.models.verification import (
        Verification,
        VerificationStatus,
        VerificationType,
    )
    from app.schemas.report import ReportResponse
    from app.services.report_service import report_service

    async with AsyncSessionLocal() as db:
        user = User(
            email=_unique_email(),
            hashed_password=get_password_hash("Str0ngPass!23"),
            full_name="Report Test",
        )
        db.add(user)
        await db.flush()

        verification = Verification(
            user_id=user.id,
            verification_type=VerificationType.COMPANY,
            company_name="Acme, Inc.",
            target_url="https://example.com",
            status=VerificationStatus.COMPLETED,
        )
        db.add(verification)
        await db.flush()

        report = await report_service.generate_report(
            db, verification_id=verification.id, user_id=user.id
        )

        # The bug surfaced here: accessing updated_at during serialization.
        payload = ReportResponse.model_validate(report)
        assert payload.status.value == "completed"
        assert payload.file_size_bytes > 0
        assert payload.created_at is not None and payload.updated_at is not None

        await db.rollback()
