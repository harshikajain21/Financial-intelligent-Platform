"""
Helpers — general-purpose utility functions.
"""

from __future__ import annotations

import functools
import time
from typing import Any, Callable, Generator, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


# ------------------------------------------------------------------
# Dict utilities
# ------------------------------------------------------------------

def flatten_dict(d: dict[str, Any], parent_key: str = "", sep: str = ".") -> dict[str, Any]:
    """Recursively flatten a nested dict into a single-level dict.

    Example::

        flatten_dict({"a": {"b": 1, "c": 2}})
        # → {"a.b": 1, "a.c": 2}
    """
    items: dict[str, Any] = {}
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.update(flatten_dict(v, new_key, sep))
        else:
            items[new_key] = v
    return items


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge `override` into `base`, returning a new dict."""
    result = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result


# ------------------------------------------------------------------
# List utilities
# ------------------------------------------------------------------

def chunk_list(lst: list[Any], size: int) -> Generator[list[Any], None, None]:
    """Yield successive chunks of `size` from `lst`.

    Example::

        list(chunk_list([1,2,3,4,5], 2))
        # → [[1, 2], [3, 4], [5]]
    """
    for i in range(0, len(lst), size):
        yield lst[i: i + size]


# ------------------------------------------------------------------
# Type coercion
# ------------------------------------------------------------------

def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float, returning `default` on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert a value to int, returning `default` on failure."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# ------------------------------------------------------------------
# Retry decorator
# ------------------------------------------------------------------

def retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """Decorator: retry a function on specified exceptions.

    Args:
        max_attempts: Maximum number of attempts (including first call).
        delay:        Initial delay between retries (seconds).
        backoff:      Multiplicative backoff factor applied to delay after each retry.
        exceptions:   Exception types to catch and retry on.

    Example::

        @retry(max_attempts=3, delay=0.5, exceptions=(requests.RequestException,))
        def fetch_data():
            ...
    """
    def decorator(fn: F) -> F:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:
                    if attempt == max_attempts:
                        raise
                    time.sleep(current_delay)
                    current_delay *= backoff
        return wrapper  # type: ignore
    return decorator


# ------------------------------------------------------------------
# Formatting helpers
# ------------------------------------------------------------------

def format_pct(value: float, decimals: int = 2) -> str:
    """Format a float as a percentage string.

    Example::

        format_pct(0.1234)  # → "12.34%"
    """
    return f"{value * 100:.{decimals}f}%"


def format_currency(value: float, symbol: str = "$", decimals: int = 2) -> str:
    """Format a float as a currency string.

    Example::

        format_currency(1234567.89)  # → "$1,234,567.89"
    """
    return f"{symbol}{value:,.{decimals}f}"
