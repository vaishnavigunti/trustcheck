"""Centralized error handlers for API."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    TrustCheckException,
    ValidationError,
    VerificationError,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


async def trustcheck_exception_handler(
    request: Request,
    exc: TrustCheckException,
) -> JSONResponse:
    """Handle custom TrustCheck exceptions."""
    logger.warning(
        "Request failed",
        error=exc.message,
        status_code=exc.status_code,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": exc.__class__.__name__,
                "message": exc.message,
            }
        },
    )


async def validation_exception_handler(
    request: Request,
    exc: ValidationError,
) -> JSONResponse:
    """Handle validation errors."""
    return await trustcheck_exception_handler(request, exc)


async def authentication_exception_handler(
    request: Request,
    exc: AuthenticationError,
) -> JSONResponse:
    """Handle authentication errors."""
    return await trustcheck_exception_handler(request, exc)


async def not_found_exception_handler(
    request: Request,
    exc: NotFoundError,
) -> JSONResponse:
    """Handle not found errors."""
    return await trustcheck_exception_handler(request, exc)


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Catch-all for unexpected errors.

    Logs the full exception server-side (with traceback) for monitoring, but
    returns a generic message so internal details / stack traces are never
    leaked to the client.
    """
    logger.error(
        "Unhandled exception",
        error=str(exc),
        error_type=exc.__class__.__name__,
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "An internal error occurred. Please try again later.",
            }
        },
    )


def setup_exception_handlers(app) -> None:
    """Register all exception handlers with FastAPI app."""
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(AuthenticationError, authentication_exception_handler)
    app.add_exception_handler(AuthorizationError, trustcheck_exception_handler)
    app.add_exception_handler(NotFoundError, not_found_exception_handler)
    app.add_exception_handler(RateLimitError, trustcheck_exception_handler)
    app.add_exception_handler(VerificationError, trustcheck_exception_handler)
    app.add_exception_handler(TrustCheckException, trustcheck_exception_handler)
    # Catch-all: must be registered for the base Exception class so anything
    # uncaught returns a sanitized 500 instead of a raw traceback.
    app.add_exception_handler(Exception, unhandled_exception_handler)
