"""Caching utilities for the bot."""
import time
from typing import Any, Dict, Optional, TypeVar, Generic
from dataclasses import dataclass

T = TypeVar("T")


@dataclass
class CacheEntry(Generic[T]):
    """Represents a cached value with expiration time."""

    value: T
    expires_at: float

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return time.time() > self.expires_at


class SimpleCache(Generic[T]):
    """Simple in-memory cache with TTL support."""

    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize cache.
        
        Args:
            ttl_seconds: Time-to-live for cached items in seconds
        """
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, CacheEntry[T]] = {}

    def get(self, key: str) -> Optional[T]:
        """
        Retrieve value from cache.
        
        Args:
            key: Cache key
        
        Returns:
            Cached value or None if not found/expired
        """
        if key not in self._cache:
            return None

        entry = self._cache[key]
        if entry.is_expired():
            del self._cache[key]
            return None

        return entry.value

    def set(self, key: str, value: T) -> None:
        """
        Store value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
        """
        expires_at = time.time() + self.ttl_seconds
        self._cache[key] = CacheEntry(value=value, expires_at=expires_at)

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()

    def size(self) -> int:
        """Get current number of valid cache entries."""
        return len(self._cache)
