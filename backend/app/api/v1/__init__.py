"""API v1 routes."""

from app.api.v1.auth import router as auth_router
from app.api.v1.reports import router as reports_router
from app.api.v1.verifications import router as verifications_router

__all__ = ["auth_router", "reports_router", "verifications_router"]
