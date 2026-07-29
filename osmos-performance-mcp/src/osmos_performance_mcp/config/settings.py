"""
Application Settings
====================
Pydantic BaseSettings, environment-driven — mirrors osmos-reporting-mcp.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    APP_NAME: str = "osPerformanceMcp"
    ENV_DOMAIN: str = "prod"
    LOG_LEVEL: str = "INFO"

    KAM_ENV_DOMAIN: str = ""  # overrides ENV_DOMAIN for KAM only; defaults to ENV_DOMAIN if unset

    # Limits
    MAX_DATE_RANGE_DAYS: int = 180
    RATE_LIMIT_CALLS: int = 60
    RATE_LIMIT_PERIOD: int = 60

    # Redis (rate limiting) — fetched from Hades by app key
    REDIS_APP_KEY: str = "OS_MCP_REDIS"

    # Response-size guard
    BYTES_PER_TOKEN: float = 2.5
    MAX_RESPONSE_TOKENS: int = 50_000

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()

# Override app name for test environments (matches org convention)
if settings.ENV_DOMAIN == "test":
    settings.APP_NAME = "irisTestApplication"
