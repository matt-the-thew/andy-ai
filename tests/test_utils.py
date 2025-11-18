"""Unit tests for utility modules."""
import unittest
import time
from utils.cache import SimpleCache
from utils.rate_limit import RateLimiter


class TestSimpleCache(unittest.TestCase):
    """Test cases for SimpleCache."""

    def setUp(self):
        """Set up test fixtures."""
        self.cache = SimpleCache(ttl_seconds=2)

    def test_cache_set_and_get(self):
        """Test setting and getting cache values."""
        self.cache.set("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")

    def test_cache_get_nonexistent(self):
        """Test getting non-existent key returns None."""
        self.assertIsNone(self.cache.get("nonexistent"))

    def test_cache_expiration(self):
        """Test cache expiration."""
        self.cache.set("key1", "value1")
        self.assertEqual(self.cache.get("key1"), "value1")

        # Wait for expiration
        time.sleep(2.1)
        self.assertIsNone(self.cache.get("key1"))

    def test_cache_clear(self):
        """Test clearing cache."""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.assertEqual(self.cache.size(), 2)

        self.cache.clear()
        self.assertEqual(self.cache.size(), 0)

    def test_cache_multiple_keys(self):
        """Test cache with multiple keys."""
        self.cache.set("key1", "value1")
        self.cache.set("key2", "value2")
        self.cache.set("key3", "value3")

        self.assertEqual(self.cache.get("key1"), "value1")
        self.assertEqual(self.cache.get("key2"), "value2")
        self.assertEqual(self.cache.get("key3"), "value3")


class TestRateLimiter(unittest.TestCase):
    """Test cases for RateLimiter."""

    def setUp(self):
        """Set up test fixtures."""
        self.limiter = RateLimiter(calls_per_minute=3)

    def test_rate_limiter_allow_first_calls(self):
        """Test rate limiter allows initial calls."""
        self.assertTrue(self.limiter.is_allowed("user1"))
        self.assertTrue(self.limiter.is_allowed("user1"))
        self.assertTrue(self.limiter.is_allowed("user1"))

    def test_rate_limiter_blocks_excess_calls(self):
        """Test rate limiter blocks excess calls."""
        # Use up the limit
        for _ in range(3):
            self.assertTrue(self.limiter.is_allowed("user1"))

        # Next call should be blocked
        self.assertFalse(self.limiter.is_allowed("user1"))

    def test_rate_limiter_separate_keys(self):
        """Test rate limiter tracks separate keys independently."""
        self.assertTrue(self.limiter.is_allowed("user1"))
        self.assertTrue(self.limiter.is_allowed("user1"))
        self.assertTrue(self.limiter.is_allowed("user1"))
        self.assertFalse(self.limiter.is_allowed("user1"))

        # user2 should have their own limit
        self.assertTrue(self.limiter.is_allowed("user2"))
        self.assertTrue(self.limiter.is_allowed("user2"))
        self.assertTrue(self.limiter.is_allowed("user2"))
        self.assertFalse(self.limiter.is_allowed("user2"))

    def test_rate_limiter_cooldown(self):
        """Test rate limiter cooldown calculation."""
        for _ in range(3):
            self.assertTrue(self.limiter.is_allowed("user1"))

        cooldown = self.limiter.get_cooldown_seconds("user1")
        self.assertGreater(cooldown, 0)
        self.assertLessEqual(cooldown, 60)

    def test_rate_limiter_cooldown_when_allowed(self):
        """Test rate limiter returns 0 cooldown when allowed."""
        cooldown = self.limiter.get_cooldown_seconds("fresh_user")
        self.assertEqual(cooldown, 0.0)


if __name__ == "__main__":
    unittest.main()
