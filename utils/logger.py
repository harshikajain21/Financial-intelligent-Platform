# utils/logger.py

import sys
from loguru import logger
from pathlib import Path
from config.settings import settings

# Create logs directory if it doesn't exist
Path("logs").mkdir(exist_ok=True)

# Remove default logger
logger.remove()

# --- Console logger (colored, readable) ---
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
           "<level>{level: <8}</level> | "
           "<cyan>{name}</cyan>:<cyan>{line}</cyan> | "
           "<level>{message}</level>",
    level="DEBUG" if settings.DEBUG else "INFO",
    colorize=True
)

# --- File logger (full detail, rotates daily) ---
logger.add(
    "logs/platform_{time:YYYY-MM-DD}.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} | {message}",
    level="DEBUG",
    rotation="00:00",        # new file every day
    retention="30 days",     # keep last 30 days
    compression="zip"        # compress old logs
)

# --- Error-only log (easy to monitor in production) ---
logger.add(
    "logs/errors.log",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{line} | {message}",
    level="ERROR",
    rotation="10 MB"
)


def get_logger(name: str):
    """
    Returns a logger bound to a specific agent/module name.
    Usage: logger = get_logger(__name__)
    """
    return logger.bind(agent=name)