"""
Application configuration using Pydantic Settings.
"""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Placeholder secrets shipped in .env / .env.example — never valid in production.
_INSECURE_SECRET_KEYS = {
    "your-super-secret-key-change-this-in-production",
    "change-this-to-a-random-64-char-string-in-production",
}


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


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
