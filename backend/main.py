"""
TrustCheck FastAPI Application Entry Point.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from app.api.errors import setup_exception_handlers
from app.api.v1 import auth_router, reports_router, verifications_router
from app.core import get_settings, setup_logging
from app.core.rate_limit import rate_limit_middleware
from app.core.security_headers import SecurityHeadersMiddleware
from app.core.database import async_engine, _is_sqlite
from app.models import Base

# Setup logging on import
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    # Startup
    settings = get_settings()
    print(f"Starting {settings.app_name} in {settings.app_env} mode")
    
    # Create tables automatically for SQLite (local development)
    if _is_sqlite(settings.database_url):
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("SQLite tables created")
    
    yield
    
    # Shutdown
    await async_engine.dispose()
    print("Application shutdown complete")


def create_application() -> FastAPI:
    """Application factory."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        description="Evidence-Based Internship & Job Offer Verification Platform",
        version="1.0.0",
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None,
        lifespan=lifespan,
    )
    
    # CORS middleware — allow any localhost / 127.0.0.1 port in dev (browser previews use random ports)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?" if not settings.is_production else None,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Trusted host middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"] if not settings.is_production else ["*.vercel.app", "*.railway.app"],
    )
    
    # Security headers middleware
    app.add_middleware(SecurityHeadersMiddleware)
    
    # Include API routers
    app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(verifications_router, prefix="/api/v1/verifications", tags=["verifications"])
    app.include_router(reports_router, prefix="/api/v1/reports", tags=["reports"])

    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Rate limiting middleware (applied to all routes except health)
    @app.middleware("http")
    async def rate_limit_handler(request: Request, call_next):
        # Skip rate limiting for health check and CORS preflight
        if request.method == "OPTIONS" or request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        return await rate_limit_middleware(request, call_next)
    
    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": settings.app_name}
    
    @app.get("/", tags=["root"])
    async def root():
        """Root endpoint."""
        return {
            "name": settings.app_name,
            "description": "Evidence-Based Internship & Job Offer Verification Platform",
            "version": "1.0.0",
        }
    
    return app


# Create application instance
app = create_application()

if __name__ == "__main__":
    import uvicorn
    
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=not settings.is_production,
        log_level=settings.log_level.lower(),
    )
