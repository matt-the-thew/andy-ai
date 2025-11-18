"""Rate limiting utilities for the bot."""
import time
from typing import Dict, Tuple
from collections import defaultdict


class RateLimiter:
    """Rate limiter to prevent abuse."""

    def __init__(self, calls_per_minute: int):
        """
        Initialize rate limiter.
        
        Args:
            calls_per_minute: Maximum calls allowed per minute per key
        """
        self.calls_per_minute = calls_per_minute
        self.min_interval = 60.0 / calls_per_minute
        self._last_call: Dict[str, float] = defaultdict(float)
        self._call_times: Dict[str, list] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        """
        Check if action is allowed for key.
        
        Args:
            key: Identifier (e.g., user_id, guild_id)
        
        Returns:
            True if action is allowed, False if rate limited
        """
        now = time.time()
        cutoff = now - 60  # Look back 60 seconds

        # Clean old entries
        if key in self._call_times:
            self._call_times[key] = [t for t in self._call_times[key] if t > cutoff]

        # Check if limit exceeded
        if len(self._call_times[key]) >= self.calls_per_minute:
            return False

        self._call_times[key].append(now)
        self._last_call[key] = now
        return True

    def get_cooldown_seconds(self, key: str) -> float:
        """
        Get seconds until next call is allowed.
        
        Args:
            key: Identifier
        
        Returns:
            Seconds to wait (0 if call is allowed now)
        """
        if self.is_allowed(key):
            return 0.0

        cutoff = time.time() - 60
        valid_times = [t for t in self._call_times.get(key, []) if t > cutoff]

        if not valid_times:
            return 0.0

        oldest_call = min(valid_times)
        return max(0.0, 60 - (time.time() - oldest_call))
