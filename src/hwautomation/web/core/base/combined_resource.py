"""
Combined base resource class for HWAutomation web interface.

This module provides BaseResource class that combines all mixins to provide
a complete foundation for API resources with RESTful patterns, database
operations, validation, caching, and timestamp utilities.
"""

from typing import Any, Callable

from .cache_mixin import CacheMixin
from .database_mixin import DatabaseMixin
from .resource_view import BaseResourceView
from .timestamp_mixin import TimestampMixin
from .validation_mixin import ValidationMixin


class BaseResource(
    BaseResourceView, DatabaseMixin, ValidationMixin, CacheMixin, TimestampMixin
):
    """
    Combined base class for resources with all mixins.

    This provides a complete foundation for API resources with:
    - RESTful patterns
    - Database operations
    - Validation
    - Caching
    - Timestamp utilities
    """

    def __init__(self):
        super().__init__()
        DatabaseMixin.__init__(self)
        CacheMixin.__init__(self)

    def get_cached_or_fetch(
        self, cache_key: str, fetch_func: Callable, ttl: int = 300
    ) -> Any:
        """Get from cache or fetch if not cached."""
        cached_value = self.cache_get(cache_key, ttl)
        if cached_value is not None:
            return cached_value

        value = fetch_func()
        self.cache_set(cache_key, value)
        return value
