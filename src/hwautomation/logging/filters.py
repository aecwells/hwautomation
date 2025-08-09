"""
Custom log filters for HWAutomation.

This module provides specialized filters for log processing:
- CorrelationFilter: Adds correlation IDs for request tracing
- ComponentFilter: Filters by component/module name
- LevelRangeFilter: Filter by log level ranges
- RateLimitFilter: Prevents log spam with rate limiting
- EnvironmentFilter: Environment-specific filtering
"""

import logging
import threading
import time
from collections import defaultdict
from typing import Dict, Optional, Set, Tuple


class CorrelationFilter(logging.Filter):
    """
    Filter that adds correlation IDs to log records for request tracing.

    Features:
    - Automatic correlation ID injection
    - Thread-local storage for correlation IDs
    - Request/response correlation tracking
    - Cross-service correlation support
    """

    def __init__(self):
        super().__init__()
        self._local = threading.local()

    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to log record."""
        # Get correlation ID from thread-local storage
        correlation_id = getattr(self._local, "correlation_id", None)

        # If no correlation ID exists, check record attributes
        if not correlation_id:
            correlation_id = getattr(record, "correlation_id", "N/A")

        # Add correlation ID to record
        record.correlation_id = correlation_id
        return True

    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for current thread."""
        self._local.correlation_id = correlation_id

    def get_correlation_id(self) -> Optional[str]:
        """Get correlation ID for current thread."""
        return getattr(self._local, "correlation_id", None)

    def clear_correlation_id(self):
        """Clear correlation ID for current thread."""
        if hasattr(self._local, "correlation_id"):
            delattr(self._local, "correlation_id")


class ComponentFilter(logging.Filter):
    """
    Filter logs by component/module name with pattern matching.

    Features:
    - Include/exclude patterns
    - Wildcard matching support
    - Component hierarchy filtering
    - Dynamic filter updates
    """

    def __init__(
        self,
        include_patterns: Optional[Set[str]] = None,
        exclude_patterns: Optional[Set[str]] = None,
    ):
        super().__init__()
        self.include_patterns = include_patterns or set()
        self.exclude_patterns = exclude_patterns or set()

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter based on component patterns."""
        component = record.name

        # Check exclude patterns first
        for pattern in self.exclude_patterns:
            if self._matches_pattern(component, pattern):
                return False

        # If no include patterns, allow all (unless excluded)
        if not self.include_patterns:
            return True

        # Check include patterns
        for pattern in self.include_patterns:
            if self._matches_pattern(component, pattern):
                return True

        return False

    def _matches_pattern(self, component: str, pattern: str) -> bool:
        """Check if component matches pattern with wildcards."""
        if pattern == "*":
            return True

        if pattern.endswith("*"):
            return component.startswith(pattern[:-1])

        if pattern.startswith("*"):
            return component.endswith(pattern[1:])

        return component == pattern

    def add_include_pattern(self, pattern: str):
        """Add include pattern."""
        self.include_patterns.add(pattern)

    def add_exclude_pattern(self, pattern: str):
        """Add exclude pattern."""
        self.exclude_patterns.add(pattern)

    def remove_include_pattern(self, pattern: str):
        """Remove include pattern."""
        self.include_patterns.discard(pattern)

    def remove_exclude_pattern(self, pattern: str):
        """Remove exclude pattern."""
        self.exclude_patterns.discard(pattern)


class LevelRangeFilter(logging.Filter):
    """
    Filter logs by level ranges for fine-grained control.

    Features:
    - Min/max level filtering
    - Multiple level ranges
    - Component-specific level overrides
    - Dynamic level adjustments
    """

    def __init__(
        self, min_level: int = logging.NOTSET, max_level: int = logging.CRITICAL
    ):
        super().__init__()
        self.min_level = min_level
        self.max_level = max_level
        self.component_overrides: Dict[str, Tuple[int, int]] = {}

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter based on level ranges."""
        # Check for component-specific overrides
        component = record.name
        if component in self.component_overrides:
            min_level, max_level = self.component_overrides[component]
        else:
            min_level, max_level = self.min_level, self.max_level

        return min_level <= record.levelno <= max_level

    def set_component_levels(self, component: str, min_level: int, max_level: int):
        """Set level range for specific component."""
        self.component_overrides[component] = (min_level, max_level)

    def remove_component_override(self, component: str):
        """Remove component-specific override."""
        self.component_overrides.pop(component, None)


class RateLimitFilter(logging.Filter):
    """
    Rate limiting filter to prevent log spam.

    Features:
    - Configurable rate limits per component
    - Time window based limiting
    - Burst allowance
    - Spam detection and suppression
    """

    def __init__(
        self, max_rate: float = 10.0, window_size: float = 60.0, burst_size: int = 20
    ):
        super().__init__()
        self.max_rate = max_rate  # messages per second
        self.window_size = window_size  # time window in seconds
        self.burst_size = burst_size  # burst allowance

        # Track message counts per component
        self.message_counts: Dict[str, list] = defaultdict(list)
        self.suppressed_counts: Dict[str, int] = defaultdict(int)
        self.last_log_times: Dict[str, float] = defaultdict(float)

    def filter(self, record: logging.LogRecord) -> bool:
        """Apply rate limiting."""
        component = record.name
        current_time = time.time()

        # Clean old entries
        self._cleanup_old_entries(component, current_time)

        # Check burst limit
        if len(self.message_counts[component]) >= self.burst_size:
            self.suppressed_counts[component] += 1
            return False

        # Check rate limit
        recent_messages = len(self.message_counts[component])
        if recent_messages > 0:
            time_span = current_time - self.message_counts[component][0]
            if time_span > 0:
                current_rate = recent_messages / time_span
                if current_rate > self.max_rate:
                    self.suppressed_counts[component] += 1
                    return False

        # Record this message
        self.message_counts[component].append(current_time)

        # Add suppression info if any messages were suppressed
        if self.suppressed_counts[component] > 0:
            suppressed = self.suppressed_counts[component]
            record.msg = f"{record.msg} (suppressed {suppressed} similar messages)"
            self.suppressed_counts[component] = 0

        self.last_log_times[component] = current_time
        return True

    def _cleanup_old_entries(self, component: str, current_time: float):
        """Remove entries outside the time window."""
        cutoff_time = current_time - self.window_size
        self.message_counts[component] = [
            t for t in self.message_counts[component] if t > cutoff_time
        ]


class EnvironmentFilter(logging.Filter):
    """
    Environment-specific filtering for development/staging/production.

    Features:
    - Environment-based log level adjustment
    - Development-specific debug logging
    - Production noise reduction
    - Sensitive data filtering
    """

    def __init__(self, environment: str = "development"):
        super().__init__()
        self.environment = environment.lower()

        # Define environment-specific rules
        self.environment_rules = {
            "development": {
                "min_level": logging.DEBUG,
                "sensitive_filter": False,
                "debug_modules": ["*"],
            },
            "staging": {
                "min_level": logging.INFO,
                "sensitive_filter": True,
                "debug_modules": ["hwautomation.testing", "hwautomation.validation"],
            },
            "production": {
                "min_level": logging.WARNING,
                "sensitive_filter": True,
                "debug_modules": [],
            },
        }

    def filter(self, record: logging.LogRecord) -> bool:
        """Apply environment-specific filtering."""
        rules = self.environment_rules.get(
            self.environment, self.environment_rules["development"]
        )

        # Check minimum level
        min_level = rules["min_level"]
        if isinstance(min_level, int) and record.levelno < min_level:
            # Allow debug from specific modules in staging
            debug_modules = rules.get("debug_modules", [])
            if (
                self.environment == "staging"
                and record.levelno >= logging.DEBUG
                and isinstance(debug_modules, list)
                and self._is_debug_module(record.name, debug_modules)
            ):
                pass  # Allow this debug message
            else:
                return False

        # Filter sensitive data in non-development environments
        if rules["sensitive_filter"]:
            self._filter_sensitive_data(record)

        return True

    def _is_debug_module(self, module_name: str, debug_modules: list) -> bool:
        """Check if module is in debug allowlist."""
        for pattern in debug_modules:
            if pattern == "*" or module_name.startswith(pattern):
                return True
        return False

    def _filter_sensitive_data(self, record: logging.LogRecord):
        """Remove sensitive data from log messages."""
        message = record.getMessage()

        # Simple sensitive data patterns (in production, use more sophisticated filtering)
        sensitive_patterns = [
            ("password=", "password=***"),
            ("token=", "token=***"),
            ("secret=", "secret=***"),
            ("key=", "key=***"),
        ]

        for pattern, replacement in sensitive_patterns:
            if pattern in message.lower():
                # Replace sensitive value with stars
                parts = message.split(pattern)
                if len(parts) > 1:
                    value_part = parts[1].split()[0] if parts[1] else ""
                    message = message.replace(f"{pattern}{value_part}", replacement)

        # Update record message
        record.msg = message
        record.args = ()


class ContextFilter(logging.Filter):
    """
    Filter that adds contextual information to log records.

    Features:
    - Request/session context
    - User information
    - Operation context
    - Performance timing
    """

    def __init__(self):
        super().__init__()
        self._local = threading.local()

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context information to log record."""
        # Add context from thread-local storage
        context = getattr(self._local, "context", {})

        for key, value in context.items():
            if not hasattr(record, key):
                setattr(record, key, value)

        # Add timing context if available
        start_time = getattr(self._local, "operation_start", None)
        if start_time:
            elapsed = time.time() - start_time
            record.operation_duration = f"{elapsed:.3f}s"

        return True

    def set_context(self, **kwargs):
        """Set context for current thread."""
        if not hasattr(self._local, "context"):
            self._local.context = {}
        self._local.context.update(kwargs)

    def clear_context(self):
        """Clear context for current thread."""
        if hasattr(self._local, "context"):
            self._local.context.clear()

    def start_operation(self):
        """Mark operation start time."""
        self._local.operation_start = time.time()

    def end_operation(self):
        """Clear operation start time."""
        if hasattr(self._local, "operation_start"):
            delattr(self._local, "operation_start")
