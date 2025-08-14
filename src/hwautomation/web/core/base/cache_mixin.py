"""
Cache mixin for HWAutomation web interface.

This module provides CacheMixin with in-memory caching functionality,
TTL (time-to-live) support, and cache management utilities.
"""

import time
from typing import Any, Dict, Optional


class CacheMixin:
    """
    Mixin providing in-memory caching functionality.

    Features:
    - TTL-based caching
    - Cache invalidation
    - Memory management
    - Performance optimization
    """

    def __init__(self):
        if not hasattr(self, "_cache"):
            self._cache: Dict[str, Dict[str, Any]] = {}

    def cache_get(self, key: str, ttl: int = 300) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key not in self._cache:
            return None

        cache_entry = self._cache[key]
        cache_time = cache_entry.get("timestamp", 0)
        current_time = time.time()

        # Check if cache entry is expired
        if current_time - cache_time > ttl:
            # Remove expired entry
            del self._cache[key]
            return None

        return cache_entry.get("value")

    def cache_set(self, key: str, value: Any) -> None:
        """Set value in cache with timestamp."""
        self._cache[key] = {
            "value": value,
            "timestamp": time.time(),
        }

    def cache_delete(self, key: str) -> bool:
        """Delete specific cache entry."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def cache_clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()

    def cache_cleanup(self, ttl: int = 300) -> int:
        """Remove expired cache entries and return count of removed items."""
        current_time = time.time()
        expired_keys = []

        for key, cache_entry in self._cache.items():
            cache_time = cache_entry.get("timestamp", 0)
            if current_time - cache_time > ttl:
                expired_keys.append(key)

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)

    def cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        current_time = time.time()
        total_entries = len(self._cache)

        if total_entries == 0:
            return {
                "total_entries": 0,
                "expired_entries": 0,
                "valid_entries": 0,
                "memory_usage_kb": 0,
            }

        expired_count = 0
        oldest_timestamp = current_time
        newest_timestamp = 0

        for cache_entry in self._cache.values():
            timestamp = cache_entry.get("timestamp", 0)

            # Count expired entries (using default TTL of 5 minutes)
            if current_time - timestamp > 300:
                expired_count += 1

            # Track timestamp range
            oldest_timestamp = min(oldest_timestamp, timestamp)
            newest_timestamp = max(newest_timestamp, timestamp)

        # Rough memory usage estimation
        memory_usage = sum(
            len(str(key)) + len(str(entry)) for key, entry in self._cache.items()
        )

        return {
            "total_entries": total_entries,
            "expired_entries": expired_count,
            "valid_entries": total_entries - expired_count,
            "memory_usage_kb": memory_usage // 1024,
            "oldest_entry_age_seconds": (
                current_time - oldest_timestamp
                if oldest_timestamp < current_time
                else 0
            ),
            "newest_entry_age_seconds": (
                current_time - newest_timestamp if newest_timestamp > 0 else 0
            ),
        }

    def cache_has(self, key: str, ttl: int = 300) -> bool:
        """Check if cache has valid (non-expired) entry for key."""
        return self.cache_get(key, ttl) is not None
