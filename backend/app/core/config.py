"""
Application configuration using Pydantic Settings.
"""

import re
import socket
from functools import lru_cache
from pathlib import Path
from typing import List
from urllib.parse import urlsplit

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Placeholder secrets shipped in .env / .env.example — never valid in production.
_INSECURE_SECRET_KEYS = {
    "your-super-secret-key-change-this-in-production",
    "change-this-to-a-random-64-char-string-in-production",
}


def _to_ipv4_host(url: str) -> str:
    """Rewrite a DB URL's hostname to a resolved IPv4 address.

    Supabase's pooler hostname resolves to NAT64 (64:ff9b::/96) IPv6
    addresses alongside its real IPv4 ones. Platforms without a working
    NAT64 gateway (e.g. Railway) try the IPv6 address first and silently
    hang instead of failing over. Resolving to IPv4 up front sidesteps this
    for every driver — psycopg2/libpq does its own DNS resolution in C,
    bypassing any Python-level socket patch.
    """
    hostname = urlsplit(url).hostname
    if not hostname or hostname in ("localhost", "127.0.0.1"):
        return url
    try:
        ipv4 = socket.getaddrinfo(hostname, None, socket.AF_INET)[0][4][0]
    except socket.gaierror:
        return url
    return re.sub(rf"@{re.escape(hostname)}(?=[:/])", f"@{ipv4}", url, count=1)


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = Field(default="TrustCheck")
    app_env: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # Server
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)

    # Database
    # For Supabase: postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres
    # For local SQLite (no setup): sqlite+aiosqlite:///./trustcheck.db
    database_url: str = Field(default="sqlite+aiosqlite:///./trustcheck.db")
    database_url_sync: str = Field(default="sqlite:///./trustcheck.db")

    # Security
    secret_key: str = Field(...)
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=15)
    refresh_token_expire_days: int = Field(default=30)

    # File Upload
    max_file_size_mb: int = Field(default=10)
    upload_dir: str = Field(default="uploads")
    allowed_extensions: str = Field(default="pdf")

    # Verification Engine
    request_timeout_seconds: int = Field(default=10)
    max_retries: int = Field(default=3)
    whois_timeout_seconds: int = Field(default=5)

    # Public Report URLs
    public_report_token_expire_days: int = Field(default=30)

    # CORS — comma-separated list of allowed frontend origins (used in production).
    # Example: "https://trustcheck.vercel.app,https://www.trustcheck.app"
    cors_origins: str = Field(default="")

    # Trusted Host headers (TrustedHostMiddleware) — comma-separated.
    # Empty = allow all hosts, which is safe behind a managed PaaS proxy
    # (Render/Vercel/Railway) that already routes by host and terminates TLS.
    # Lock down later, e.g. "trustcheck.onrender.com,api.trustcheck.app".
    allowed_hosts: str = Field(default="")

    @field_validator("allowed_extensions")
    @classmethod
    def parse_allowed_extensions(cls, v: str) -> List[str]:
        """Parse comma-separated extensions into list."""
        return [ext.strip().lower() for ext in v.split(",")]

    @property
    def max_file_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.max_file_size_mb * 1024 * 1024

    @property
    def upload_path(self) -> Path:
        """Get upload directory as Path object."""
        return Path(self.upload_dir).resolve()

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env.lower() == "production"

    @property
    def allowed_origins(self) -> List[str]:
        """Get CORS allowed origins based on environment."""
        # Explicit configuration always wins (production deployments should set this).
        if self.cors_origins.strip():
            return [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        if self.is_production:
            return ["https://trustcheck.vercel.app"]
        return ["http://localhost:3000", "http://127.0.0.1:3000"]

    @property
    def trusted_hosts(self) -> List[str]:
        """Allowed Host headers for TrustedHostMiddleware.

        Defaults to ["*"] (all hosts) so platform health checks and custom
        domains work out of the box; set ALLOWED_HOSTS to restrict.
        """
        if self.allowed_hosts.strip():
            return [h.strip() for h in self.allowed_hosts.split(",") if h.strip()]
        return ["*"]

    @model_validator(mode="after")
    def _validate_production_secret(self) -> "Settings":
        """Refuse to start in production with a weak or placeholder SECRET_KEY."""
        if self.is_production and (
            self.secret_key in _INSECURE_SECRET_KEYS or len(self.secret_key) < 32
        ):
            raise ValueError(
                "SECRET_KEY must be a strong, unique value of at least 32 "
                "characters in production. Generate one with: "
                "python -c \"import secrets; print(secrets.token_urlsafe(48))\""
            )
        return self

    @model_validator(mode="after")
    def _force_ipv4_database_hosts(self) -> "Settings":
        """Pin database URLs to a resolved IPv4 address (see _to_ipv4_host)."""
        self.database_url = _to_ipv4_host(self.database_url)
        self.database_url_sync = _to_ipv4_host(self.database_url_sync)
        return self


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
