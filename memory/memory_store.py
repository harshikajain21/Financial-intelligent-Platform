"""
Memory Store — persists agent conversation history and analysis context
for stateful multi-turn interactions and agent self-improvement.

Backends:
  - In-memory (default, non-persistent)
  - Redis (optional, configurable via settings)
"""

from __future__ import annotations

import json
import time
from collections import deque
from typing import Any

from utils.logger import get_logger

logger = get_logger("MemoryStore")


class MemoryStore:
    """Stores and retrieves agent memory entries.

    Entries are stored as:
    {
        "timestamp": float,
        "agent": str,
        "key": str,
        "value": Any,
        "ttl": float | None,  # Unix expiry timestamp
    }
    """

    def __init__(
        self,
        backend: str = "memory",
        max_entries: int = 10_000,
        redis_url: str | None = None,
    ) -> None:
        self.backend = backend
        self._store: dict[str, dict[str, Any]] = {}
        self._history: deque[dict[str, Any]] = deque(maxlen=max_entries)

        if backend == "redis":
            self._init_redis(redis_url)

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def set(self, key: str, value: Any, agent: str = "system", ttl_seconds: float | None = None) -> None:
        """Store a value under `key`.

        Args:
            key:         Storage key.
            value:       JSON-serialisable value.
            agent:       Name of the storing agent.
            ttl_seconds: Time-to-live in seconds. None → persist indefinitely.
        """
        expiry = time.time() + ttl_seconds if ttl_seconds else None
        entry = {
            "timestamp": time.time(),
            "agent": agent,
            "key": key,
            "value": value,
            "ttl": expiry,
        }

        if self.backend == "redis" and self._redis:
            raw = json.dumps(value)
            if ttl_seconds:
                self._redis.setex(key, int(ttl_seconds), raw)
            else:
                self._redis.set(key, raw)
        else:
            self._store[key] = entry

        self._history.append(entry)
        logger.debug("Memory SET key=%s agent=%s", key, agent)

    def get(self, key: str) -> Any | None:
        """Retrieve a value by key.  Returns None if missing or expired."""
        if self.backend == "redis" and self._redis:
            raw = self._redis.get(key)
            return json.loads(raw) if raw else None

        entry = self._store.get(key)
        if not entry:
            return None

        # Check TTL
        if entry.get("ttl") and time.time() > entry["ttl"]:
            del self._store[key]
            return None

        return entry["value"]

    def delete(self, key: str) -> None:
        """Remove a key from the store."""
        if self.backend == "redis" and self._redis:
            self._redis.delete(key)
        else:
            self._store.pop(key, None)

    def keys(self, prefix: str = "") -> list[str]:
        """List all keys, optionally filtered by prefix."""
        if self.backend == "redis" and self._redis:
            return [k.decode() for k in self._redis.keys(f"{prefix}*")]
        return [k for k in self._store if k.startswith(prefix)]

    def history(self, agent: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        """Return recent memory entries, optionally filtered by agent."""
        entries = list(self._history)
        if agent:
            entries = [e for e in entries if e["agent"] == agent]
        return entries[-limit:]

    def clear(self) -> None:
        """Clear all stored entries."""
        self._store.clear()
        self._history.clear()
        logger.info("MemoryStore cleared.")

    # ------------------------------------------------------------------
    # Redis setup
    # ------------------------------------------------------------------

    def _init_redis(self, redis_url: str | None) -> None:
        try:
            import redis  # type: ignore

            url = redis_url or "redis://localhost:6379/0"
            self._redis = redis.from_url(url, decode_responses=False)
            self._redis.ping()
            logger.info("Connected to Redis at %s.", url)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Redis unavailable (%s). Falling back to in-memory.", exc)
            self.backend = "memory"
            self._redis = None
    
    _redis = None

    def __repr__(self) -> str:
        return f"<MemoryStore backend={self.backend} entries={len(self._store)}>"
