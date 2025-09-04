import logging
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    ENV: str = "development"
    DEBUG: bool = False
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DRAMATIQ_BROKER_URL: str = Field(..., env="DRAMATIQ_BROKER_URL")
    SECRET_KEY: str = Field(..., env="SECRET_KEY")
    BASE_DIR: str = Field(
        default=Path(__file__).resolve().parent.as_posix(),
        env="BASE_DIR",
        description="Base directory for the application",
    )
    ALLOWED_ORIGINS: list[str] = Field(
        default=["*"],
        env="ALLOWED_ORIGINS",
        description="List of allowed origins for CORS",
    )
    FRONTEND_URL: str = Field(
        default="http://localhost:5173",
        env="FRONTEND_URL",
        description="URL of the frontend application",
    )
    IG_USERNAME: str = Field(..., env="IG_USERNAME")
    IG_PASSWORD: str = Field(..., env="IG_PASSWORD")
    IG_API_KEY: str = Field(..., env="IG_API_KEY")
    IG_DEMO_API_BASE_URL: str = Field(
        "https://demo-api.ig.com/gateway/deal/",
        env="IG_DEMO_API_BASE_URL",
        description="Base URL for the IG API",
    )
    IG_ACCOUNT_ID: str = Field(
        ...,
        env="IG_ACCOUNT_ID",
        description="Account ID for IG trading",
    )
    IG_LIVE_API_BASE_URL: str = Field(
        "https://api.ig.com/gateway/deal/",
        env="IG_LIVE_API_BASE_URL",
        description="Base URL for the IG live API",
    )
    ACCESS_TOKEN_LIFETIME_IN_SECONDS: int = Field(
        default=600,  # 10 minutes
        env="ACCESS_TOKEN_LIFETIME_IN_SECONDS",
        description="Lifetime of access tokens in seconds",
    )
    REFRESH_TOKEN_LIFETIME_IN_SECONDS: int = Field(
        default=3600,  # 1 hour
        env="REFRESH_TOKEN_LIFETIME_IN_SECONDS",
        description="Lifetime of refresh tokens in seconds",
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        env="JWT_ALGORITHM",
        description="Algorithm used for signing JWT tokens",
    )
    DEV_ACCESS_TOKEN_LIFETIME_IN_SECONDS: int = Field(
        default=3600,  # 1 hour
        env="DEV_ACCESS_TOKEN_LIFETIME_IN_SECONDS",
        description="Lifetime of access tokens in development mode in seconds",
    )
    SMTP_USERNAME: str = Field(..., env="SMTP_USERNAME")
    SMTP_PASSWORD: str = Field(..., env="SMTP_PASSWORD")
    SMTP_HOST: str = Field(..., env="SMTP_HOST")
    SMTP_PORT: int = Field(..., env="SMTP_PORT")
    FROM_EMAIL: str = Field(
        "admin@autotrader.eti-ini.me",
        env="FROM_EMAIL",
        description="Email address from which emails are sent",
    )
    DIVIDEND_DATE_UPDATE_SCHEDULE: str = Field(
        default="0 0 * * 6",
        env="DIVIDEND_DATE_UPDATE_SCHEDULE",
        description="Cron expression for dividend date update schedule (default: midnight on Saturday)",
    )
    ORDER_CLEANUP_SCHEDULE: str = Field(
        default="0 0 * * *",  # Every day at midnight
        env="ORDER_CLEANUP_SCHEDULE",
        description="Cron expression for order cleanup schedule (default: every day)",
    )
    ORDER_CLEANUP_HOURS: int = Field(
        default=24,
        env="ORDER_CLEANUP_HOURS",
        description="Number of hours after which orders should be deleted (default: 8 hours)",
    )
    ORDER_CONVERSION_CHECK_SCHEDULE: str = Field(
        default="* * * * *",  # Every minute
        env="ORDER_CONVERSION_CHECK_SCHEDULE",
        description="Cron expression for order conversion check schedule (default: every minute)",
    )
    WEBHOOK_SECRET_LENGTH: int = Field(
        default=32,
        env="WEBHOOK_SECRET_LENGTH",
        description="Length of the webhook secret key",
    )
    DEFAULT_CURRENCY_CODE: str = Field(
        default="GBP",
        env="DEFAULT_CURRENCY_CODE",
        description="Default currency code for the application",
    )
    LOGFILE_NAME_PREFIX: str = Field(
        default="auto_trader_",
        env="LOGFILE_NAME_PREFIX",
        description="Prefix for log file names",
    )
    LOG_LEVEL: int = Field(
        default=logging.INFO,
        env="LOG_LEVEL",
        description="Logging level for the application",
    )

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
        },
    },
    "loggers": {
        "app": {
            "level": settings.LOG_LEVEL,
            "handlers": ["console"],
            "propagate": False,
        },
    },
    "root": {"level": settings.LOG_LEVEL, "handlers": ["console"], "propagate": False},
}
