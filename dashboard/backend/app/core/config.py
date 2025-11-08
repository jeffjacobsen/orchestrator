"""
Application configuration using Pydantic settings.
"""
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    api_reload: bool = Field(default=True, alias="API_RELOAD")

    # Database Configuration
    database_url: str = Field(
        default="sqlite+aiosqlite:///./orchestrator.db",
        alias="DATABASE_URL"
    )

    # Security
    secret_key: str = Field(
        default="dev-secret-key-change-in-production",
        alias="SECRET_KEY"
    )
    api_key: str = Field(
        default="dev-api-key-change-in-production",
        alias="API_KEY"
    )
    algorithm: str = Field(default="HS256", alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=60,
        alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:5173", "http://localhost:3000"],
        alias="CORS_ORIGINS"
    )

    # Orchestrator Integration
    orchestrator_data_dir: str = Field(
        default="../../data",
        alias="ORCHESTRATOR_DATA_DIR"
    )
    orchestrator_working_directory: str = Field(
        default="../../../../..",  # Points to orchestrator root (5 levels up from app/api/v1/)
        alias="ORCHESTRATOR_WORKING_DIRECTORY"
    )

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
