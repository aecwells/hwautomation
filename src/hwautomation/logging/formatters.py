"""
Custom log formatters for HWAutomation.

This module provides specialized formatters for different logging needs:
- StructuredFormatter: Adds context information to log records
- JSONFormatter: JSON output for production environments
- DashboardFormatter: Optimized for web dashboard display
- DebugFormatter: Enhanced debugging information
"""

import json
import logging
from typing import Any, Dict, Optional


class StructuredFormatter(logging.Formatter):
    """
    Structured formatter that adds context information to log records.

    Features:
    - Adds correlation IDs for request tracing
    - Includes module context for better debugging
    - Consistent formatting across all components
    """

    def format(self, record: logging.LogRecord) -> str:
        # Add correlation ID if available
        if hasattr(record, "correlation_id"):
            record.correlation_id = getattr(record, "correlation_id", "N/A")
        else:
            record.correlation_id = "N/A"

        # Add module context for cleaner display
        record.module_context = (
            record.name.split(".")[-1] if "." in record.name else record.name
        )

        # Add process context for multi-process environments
        record.process_name = getattr(record, "processName", "main")

        return super().format(record)


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging in production environments.

    Features:
    - Machine-readable JSON output
    - Includes all relevant log metadata
    - Compatible with log aggregation systems (ELK, Splunk, etc.)
    - Handles exceptions and stack traces
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.excluded_fields = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "exc_info",
            "exc_text",
            "stack_info",
            "getMessage",
        }

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "module": getattr(record, "module", record.name.split(".")[-1]),
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", "N/A"),
            "process": record.process,
            "thread": record.thread,
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields from the log record
        for key, value in record.__dict__.items():
            if key not in self.excluded_fields:
                log_entry[f"extra_{key}"] = value

        return json.dumps(log_entry, default=str)


class DashboardFormatter(logging.Formatter):
    """
    Specialized formatter for web dashboard display.

    Features:
    - Optimized for HTML display
    - Shorter format for better readability
    - Color-coding hints for different log levels
    - Component-based organization
    """

    def format(self, record: logging.LogRecord) -> str:
        # Create a clean component name for dashboard display
        component = record.name.split(".")[-1] if "." in record.name else record.name

        # Add severity indicator for frontend styling
        record.severity_class = f"log-{record.levelname.lower()}"
        record.component_name = component

        # Truncate long messages for dashboard display
        message = record.getMessage()
        if len(message) > 200:
            message = message[:197] + "..."
        record.truncated_message = message

        return super().format(record)


class DebugFormatter(logging.Formatter):
    """
    Enhanced formatter for development and debugging.

    Features:
    - Includes detailed context information
    - Shows file paths and line numbers
    - Includes thread and process information
    - Extra verbose for troubleshooting
    """

    def format(self, record: logging.LogRecord) -> str:
        # Add detailed context for debugging
        record.short_filename = record.filename
        record.correlation_display = getattr(record, "correlation_id", "N/A")[:8]

        # Add timing information
        record.relative_time = f"{record.relativeCreated:.0f}ms"

        # Add thread/process info for concurrent debugging
        record.thread_info = f"T{record.thread}"
        record.process_info = f"P{record.process}"

        return super().format(record)


class PerformanceFormatter(logging.Formatter):
    """
    High-performance formatter optimized for minimal overhead.

    Features:
    - Minimal string operations
    - Pre-computed format strings
    - Optimized for high-volume logging
    - Reduced memory allocations
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-compile format for performance
        self._base_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"

    def format(self, record: logging.LogRecord) -> str:
        # Use minimal formatting for performance
        return self._base_format % {
            "asctime": self.formatTime(record),
            "levelname": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }


class MultilineFormatter(logging.Formatter):
    """
    Formatter that handles multi-line messages elegantly.

    Features:
    - Proper indentation for multi-line messages
    - Stack trace formatting
    - Configuration dump formatting
    - Command output formatting
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.indent = "    "  # 4 spaces for continuation lines

    def format(self, record: logging.LogRecord) -> str:
        formatted = super().format(record)

        # Handle multi-line messages
        lines = formatted.split("\n")
        if len(lines) > 1:
            # Indent continuation lines
            for i in range(1, len(lines)):
                lines[i] = self.indent + lines[i]
            formatted = "\n".join(lines)

        return formatted
