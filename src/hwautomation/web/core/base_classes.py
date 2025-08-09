"""
Base classes and mixins for HWAutomation Web Interface.

This module provides reusable base classes for views, resources,
and common patterns in the web interface.
"""

import abc
import datetime
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from flask import g, jsonify, request
from flask.views import View

from hwautomation.database import DbHelper
from hwautomation.logging import get_logger

logger = get_logger(__name__)


class BaseAPIView(View):
    """
    Base class for all API views with common functionality.

    Features:
    - Standard response formatting
    - Error handling
    - Pagination support
    - Request validation
    - Logging integration
    """

    methods = ["GET", "POST", "PUT", "DELETE"]

    def __init__(self):
        self.db_helper = DbHelper()
        self.start_time = time.time()

    def dispatch_request(self, *args, **kwargs):
        """Handle request dispatch with common processing."""
        try:
            # Log request start
            logger.info(
                f"API request started: {request.method} {request.endpoint}",
                extra={
                    "endpoint": request.endpoint,
                    "method": request.method,
                    "args": args,
                    "kwargs": kwargs,
                },
            )

            # Call the appropriate method
            handler = getattr(self, request.method.lower(), None)
            if handler is None:
                return self.method_not_allowed()

            result = handler(*args, **kwargs)

            # Log successful completion
            duration = time.time() - self.start_time
            logger.info(
                f"API request completed: {request.method} {request.endpoint} "
                f"in {duration:.3f}s",
                extra={
                    "endpoint": request.endpoint,
                    "method": request.method,
                    "duration": duration,
                    "status": "success",
                },
            )

            return result

        except Exception as e:
            return self.handle_error(e)

    def method_not_allowed(self):
        """Handle method not allowed."""
        return self.error_response("Method not allowed", "METHOD_NOT_ALLOWED", 405)

    def handle_error(self, error: Exception):
        """Handle unexpected errors."""
        duration = time.time() - self.start_time
        logger.error(
            f"API request failed: {request.method} {request.endpoint} "
            f"after {duration:.3f}s - {error}",
            extra={
                "endpoint": request.endpoint,
                "method": request.method,
                "duration": duration,
                "status": "error",
                "error_type": type(error).__name__,
            },
            exc_info=True,
        )

        return self.error_response(
            "Internal server error", "INTERNAL_SERVER_ERROR", 500
        )

    def success_response(
        self,
        data: Any = None,
        message: str = "Success",
        status_code: int = 200,
        **kwargs,
    ) -> Tuple[Dict, int]:
        """Create standardized success response."""
        response_data = {
            "success": True,
            "message": message,
            "timestamp": time.time(),
            "correlation_id": getattr(g, "correlation_id", "unknown"),
        }

        if data is not None:
            response_data["data"] = data

        # Add any additional fields
        response_data.update(kwargs)

        return jsonify(response_data), status_code

    def error_response(
        self,
        message: str,
        error_code: str,
        status_code: int,
        details: Optional[str] = None,
        **kwargs,
    ) -> Tuple[Dict, int]:
        """Create standardized error response."""
        response_data = {
            "success": False,
            "error": message,
            "error_code": error_code,
            "timestamp": time.time(),
            "correlation_id": getattr(g, "correlation_id", "unknown"),
        }

        if details:
            response_data["details"] = details

        # Add any additional fields
        response_data.update(kwargs)

        return jsonify(response_data), status_code

    def paginate_response(
        self,
        items: List[Any],
        page: int = 1,
        per_page: int = 50,
        total: Optional[int] = None,
    ) -> Dict:
        """Create paginated response."""
        if total is None:
            total = len(items)

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        page_items = items[start_idx:end_idx]

        total_pages = (total + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1

        return {
            "items": page_items,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
                "has_next": has_next,
                "has_prev": has_prev,
                "next_page": page + 1 if has_next else None,
                "prev_page": page - 1 if has_prev else None,
            },
        }


class BaseResourceView(BaseAPIView):
    """
    Base class for RESTful resource views.

    Features:
    - CRUD operations
    - Resource identification
    - Validation helpers
    - Common patterns
    """

    resource_name = "resource"

    def get(self, resource_id: Optional[str] = None):
        """Handle GET requests."""
        if resource_id:
            return self.get_single(resource_id)
        else:
            return self.get_list()

    def post(self):
        """Handle POST requests (create)."""
        return self.create()

    def put(self, resource_id: str):
        """Handle PUT requests (update)."""
        return self.update(resource_id)

    def delete(self, resource_id: str):
        """Handle DELETE requests."""
        return self.delete_resource(resource_id)

    @abc.abstractmethod
    def get_single(self, resource_id: str):
        """Get a single resource by ID."""
        pass

    @abc.abstractmethod
    def get_list(self):
        """Get a list of resources."""
        pass

    @abc.abstractmethod
    def create(self):
        """Create a new resource."""
        pass

    @abc.abstractmethod
    def update(self, resource_id: str):
        """Update an existing resource."""
        pass

    @abc.abstractmethod
    def delete_resource(self, resource_id: str):
        """Delete a resource."""
        pass

    def validate_resource_exists(self, resource_id: str) -> bool:
        """Validate that a resource exists."""
        # Override in subclasses with specific validation
        return True

    def get_request_data(self) -> Dict[str, Any]:
        """Get and validate request data."""
        if not request.is_json:
            raise ValueError("Request must be JSON")

        data = request.get_json()
        if data is None:
            raise ValueError("Invalid JSON data")

        return data


class DatabaseMixin:
    """
    Mixin providing database operations and connection management.

    Features:
    - Connection management
    - Transaction handling
    - Query helpers
    - Error handling
    """

    def __init__(self):
        if not hasattr(self, "db_helper"):
            self.db_helper = DbHelper()

    def with_connection(self, func, *args, **kwargs):
        """Execute function with database connection."""
        try:
            with self.db_helper.get_connection() as conn:
                return func(conn, *args, **kwargs)
        except Exception as e:
            logger.error(f"Database operation failed: {e}", exc_info=True)
            raise

    def execute_query(
        self,
        query: str,
        params: Tuple = (),
        fetch_one: bool = False,
        fetch_all: bool = True,
    ):
        """Execute a database query with error handling."""

        def _execute(conn):
            cursor = conn.cursor()
            cursor.execute(query, params)

            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            else:
                return cursor.rowcount

        return self.with_connection(_execute)

    def execute_many(self, query: str, params_list: List[Tuple]):
        """Execute a query with multiple parameter sets."""

        def _execute_many(conn):
            cursor = conn.cursor()
            cursor.executemany(query, params_list)
            return cursor.rowcount

        return self.with_connection(_execute_many)

    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information."""
        query = f"PRAGMA table_info({table_name})"
        rows = self.execute_query(query)

        return [
            {
                "column_id": row[0],
                "name": row[1],
                "type": row[2],
                "not_null": bool(row[3]),
                "default_value": row[4],
                "primary_key": bool(row[5]),
            }
            for row in rows
        ]


class ValidationMixin:
    """
    Mixin providing common validation patterns.

    Features:
    - Field validation
    - Type checking
    - Format validation
    - Business rules
    """

    def validate_required_fields(
        self, data: Dict[str, Any], required_fields: List[str]
    ) -> List[str]:
        """Validate required fields are present."""
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == "":
                missing_fields.append(field)
        return missing_fields

    def validate_field_types(
        self, data: Dict[str, Any], field_types: Dict[str, type]
    ) -> List[str]:
        """Validate field types."""
        invalid_fields = []
        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                invalid_fields.append(f"{field} must be {expected_type.__name__}")
        return invalid_fields

    def validate_string_length(
        self, data: Dict[str, Any], length_rules: Dict[str, Dict[str, int]]
    ) -> List[str]:
        """Validate string field lengths."""
        errors = []
        for field, rules in length_rules.items():
            if field in data and isinstance(data[field], str):
                value = data[field]
                min_length = rules.get("min", 0)
                max_length = rules.get("max", float("inf"))

                if len(value) < min_length:
                    errors.append(f"{field} must be at least {min_length} characters")
                if len(value) > max_length:
                    errors.append(f"{field} must be at most {max_length} characters")

        return errors

    def validate_ip_address(self, ip_string: str) -> bool:
        """Validate IP address format."""
        import ipaddress

        try:
            ipaddress.ip_address(ip_string)
            return True
        except ValueError:
            return False

    def validate_server_id(self, server_id: str) -> bool:
        """Validate server ID format."""
        # Server IDs should be alphanumeric with hyphens/underscores
        import re

        pattern = r"^[a-zA-Z0-9_-]+$"
        return bool(re.match(pattern, server_id))

    def validate_device_type(self, device_type: str) -> bool:
        """Validate device type format."""
        # Device types like 'a1.c5.large', 'd1.c2.medium'
        import re

        pattern = r"^[a-z]\d+\.c\d+\.(small|medium|large)$"
        return bool(re.match(pattern, device_type))


class CacheMixin:
    """
    Mixin providing caching functionality.

    Features:
    - Memory caching
    - TTL support
    - Cache invalidation
    - Statistics
    """

    def __init__(self):
        if not hasattr(self, "_cache"):
            self._cache = {}
            self._cache_timestamps = {}
            self._cache_stats = {"hits": 0, "misses": 0}

    def cache_get(self, key: str, ttl: int = 300) -> Any:
        """Get value from cache with TTL check."""
        if key in self._cache:
            timestamp = self._cache_timestamps.get(key, 0)
            if time.time() - timestamp < ttl:
                self._cache_stats["hits"] += 1
                return self._cache[key]
            else:
                # Expired
                self.cache_delete(key)

        self._cache_stats["misses"] += 1
        return None

    def cache_set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        self._cache[key] = value
        self._cache_timestamps[key] = time.time()

    def cache_delete(self, key: str) -> None:
        """Delete value from cache."""
        self._cache.pop(key, None)
        self._cache_timestamps.pop(key, None)

    def cache_clear(self) -> None:
        """Clear all cache."""
        self._cache.clear()
        self._cache_timestamps.clear()

    def cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._cache_stats["hits"] + self._cache_stats["misses"]
        hit_rate = (
            self._cache_stats["hits"] / total_requests if total_requests > 0 else 0
        )

        return {
            "hits": self._cache_stats["hits"],
            "misses": self._cache_stats["misses"],
            "total_requests": total_requests,
            "hit_rate": hit_rate,
            "cache_size": len(self._cache),
        }


class TimestampMixin:
    """
    Mixin providing timestamp utilities.

    Features:
    - Standard timestamp formats
    - Timezone handling
    - Duration calculations
    - Date parsing
    """

    @staticmethod
    def current_timestamp() -> float:
        """Get current Unix timestamp."""
        return time.time()

    @staticmethod
    def format_timestamp(timestamp: float, format_type: str = "iso") -> str:
        """Format timestamp to string."""
        dt = datetime.datetime.fromtimestamp(timestamp)

        if format_type == "iso":
            return dt.isoformat()
        elif format_type == "human":
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        elif format_type == "date":
            return dt.strftime("%Y-%m-%d")
        elif format_type == "time":
            return dt.strftime("%H:%M:%S")
        else:
            return str(timestamp)

    @staticmethod
    def parse_timestamp(timestamp_str: str) -> float:
        """Parse timestamp string to Unix timestamp."""
        try:
            # Try ISO format first
            dt = datetime.datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            return dt.timestamp()
        except ValueError:
            # Try common formats
            formats = ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%H:%M:%S"]

            for fmt in formats:
                try:
                    dt = datetime.datetime.strptime(timestamp_str, fmt)
                    return dt.timestamp()
                except ValueError:
                    continue

            raise ValueError(f"Unable to parse timestamp: {timestamp_str}")

    @staticmethod
    def duration_since(timestamp: float) -> float:
        """Calculate duration since timestamp."""
        return time.time() - timestamp

    @staticmethod
    def format_duration(duration: float) -> str:
        """Format duration in human-readable format."""
        if duration < 60:
            return f"{duration:.1f}s"
        elif duration < 3600:
            minutes = duration / 60
            return f"{minutes:.1f}m"
        else:
            hours = duration / 3600
            return f"{hours:.1f}h"


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
