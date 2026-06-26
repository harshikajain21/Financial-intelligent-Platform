# config/settings.py

from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """
    Central configuration for the entire platform.
    Reads from .env file automatically.
    lru_cache (below) ensures this is only loaded once.
    """

    # --- App ---
    APP_NAME: str = "Financial Intelligence Platform"
    DEBUG: bool = False
    VERSION: str = "0.1.0"

    # --- LLM ---
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"       # cheap & fast for dev

    # --- Finance APIs ---
    ALPHA_VANTAGE_API_KEY: str = ""
    FINNHUB_API_KEY: str = ""
    POLYGON_API_KEY: str = ""

    # --- Database ---
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "finplatform"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = ""

    # --- Redis ---
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # --- Alerts ---
    TELEGRAM_BOT_TOKEN: str = ""
    DISCORD_WEBHOOK_URL: str = ""

    # --- Data ---
    DEFAULT_SYMBOLS: list = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN"]
    DATA_REFRESH_INTERVAL: int = 60          # seconds

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"                     # ignore unknown .env keys


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    Call this anywhere: from config.settings import get_settings
    """
    return Settings()


# Convenience — import this directly
settings = get_settings()