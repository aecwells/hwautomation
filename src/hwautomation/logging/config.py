"""
Unified Logging Configuration for HWAutomation.

This module provides centralized logging configuration with support for:
- Environment-specific configurations
- Structured logging         if use_file_logging:
            handlers.update({
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "DEBUG",
                    "formatter": "detailed",
                    "filename": "logs/hwautomation.log",
                    "maxBytes": 5242880,  # 5MB
                    "backupCount": 3,
                },
                "error_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "ERROR",
                    "formatter": "detailed",
                    "filename": "logs/errors.log",
                    "maxBytes": 5242880,
                    "backupCount": 5,
                },
            })rformance-optimized logging
- Correlation tracking for debugging
"""

import logging
import logging.config
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

# Global logger registry
_logger_registry: Dict[str, logging.Logger] = {}


class StructuredFormatter(logging.Formatter):
    """
    Structured formatter that adds context information to log records.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Add correlation ID if available
        if hasattr(record, "correlation_id"):
            record.correlation_id = getattr(record, "correlation_id", "N/A")
        else:
            record.correlation_id = "N/A"

        # Add module context
        record.module_context = (
            record.name.split(".")[-1] if "." in record.name else record.name
        )

        return super().format(record)


class JSONFormatter(logging.Formatter):
    """
    JSON formatter for structured logging in production environments.
    """

    def format(self, record: logging.LogRecord) -> str:
        import json

        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "module": record.module if hasattr(record, "module") else "unknown",
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", "N/A"),
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in (
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
            ):
                log_entry[f"extra_{key}"] = value

        return json.dumps(log_entry)


class CorrelationFilter(logging.Filter):
    """
    Filter that adds correlation IDs to log records for request tracing.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        # Try to get correlation ID from context
        correlation_id = getattr(record, "correlation_id", None)
        if not correlation_id:
            # Try to get from thread-local storage or generate one
            import threading

            thread_local = getattr(threading.current_thread(), "correlation_id", None)
            correlation_id = thread_local or "no-correlation"

        record.correlation_id = correlation_id
        return True


def load_logging_config(
    config_path: Optional[Path] = None, environment: str = "development"
) -> Dict[str, Any]:
    """
    Load logging configuration from YAML file with environment-specific overrides.

    Args:
        config_path: Path to logging configuration file
        environment: Environment name (development, staging, production)

    Returns:
        Logging configuration dictionary
    """
    if config_path is None:
        # Default to config/logging.yaml in project root
        project_root = Path(__file__).parent.parent.parent.parent
        config_path = project_root / "config" / "logging.yaml"

    if not config_path.exists():
        return get_default_config(environment)

    try:
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        # Apply environment-specific overrides
        if "environments" in config and environment in config["environments"]:
            env_config = config["environments"][environment]
            # Merge environment-specific settings
            config.update(env_config)

        return config
    except Exception as e:
        print(f"Warning: Failed to load logging config from {config_path}: {e}")
        return get_default_config(environment)


def get_default_config(environment: str = "development") -> Dict[str, Any]:
    """
    Get default logging configuration for the specified environment.

    Args:
        environment: Environment name

    Returns:
        Default logging configuration
    """
    # Create logs directory if it doesn't exist and we have permissions
    logs_dir = Path("logs")
    use_file_logging = True
    try:
        logs_dir.mkdir(exist_ok=True)
        # Test write permissions
        test_file = logs_dir / "test_permissions.tmp"
        test_file.touch()
        test_file.unlink()
    except (PermissionError, OSError):
        use_file_logging = False

    if environment == "production":
        handlers = {
            "console": {
                "class": "logging.StreamHandler",
                "level": "WARNING",
                "formatter": "standard",
                "stream": "ext://sys.stdout",
            }
        }

        if use_file_logging:
            handlers.update(
                {
                    "file": {
                        "class": "logging.handlers.RotatingFileHandler",
                        "level": "INFO",
                        "formatter": "detailed",
                        "filename": "logs/hwautomation.log",
                        "maxBytes": 10485760,  # 10MB
                        "backupCount": 5,
                    },
                    "error_file": {
                        "class": "logging.handlers.RotatingFileHandler",
                        "level": "ERROR",
                        "formatter": "detailed",
                        "filename": "logs/errors.log",
                        "maxBytes": 10485760,
                        "backupCount": 10,
                    },
                }
            )

        handler_list = ["console"]
        if use_file_logging:
            handler_list.extend(["file", "error_file"])

        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s",
                },
            },
            "handlers": handlers,
            "loggers": {
                "hwautomation": {
                    "level": "INFO",
                    "handlers": handler_list,
                    "propagate": False,
                },
            },
            "root": {"level": "WARNING", "handlers": ["console"]},
        }
    else:  # development/staging
        handlers = {
            "console": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "detailed",
                "stream": "ext://sys.stdout",
            }
        }

        if use_file_logging:
            handlers.update(
                {
                    "file": {
                        "class": "logging.handlers.RotatingFileHandler",
                        "level": "DEBUG",
                        "formatter": "detailed",
                        "filename": "logs/hwautomation.log",
                        "maxBytes": 5242880,  # 5MB
                        "backupCount": 3,
                    },
                    "error_file": {
                        "class": "logging.handlers.RotatingFileHandler",
                        "level": "ERROR",
                        "formatter": "detailed",
                        "filename": "logs/errors.log",
                        "maxBytes": 5242880,
                        "backupCount": 5,
                    },
                }
            )

        handler_list = ["console"]
        if use_file_logging:
            handler_list.extend(["file", "error_file"])

        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                },
                "detailed": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
                },
            },
            "handlers": handlers,
            "loggers": {
                "hwautomation": {
                    "level": "DEBUG",
                    "handlers": handler_list,
                    "propagate": False,
                }
            },
            "root": {"level": "INFO", "handlers": ["console"]},
        }


def setup_logging(
    config_path: Optional[Path] = None,
    environment: Optional[str] = None,
    force_reload: bool = False,
) -> None:
    """
    Set up logging configuration for the entire application.

    Args:
        config_path: Path to logging configuration file
        environment: Environment name (auto-detected if None)
        force_reload: Force reload even if already configured
    """
    global _logger_registry  # noqa: F824

    # Don't reconfigure unless forced
    if _logger_registry and not force_reload:
        return

    # Auto-detect environment if not specified
    if environment is None:
        environment = os.getenv("HW_AUTOMATION_ENV", "development")

    # Use default configuration for now (bypass YAML issues)
    config = get_default_config(environment)

    # Apply configuration
    logging.config.dictConfig(config)

    # Store reference to prevent garbage collection
    _logger_registry["root"] = logging.getLogger()

    # Log successful configuration
    logger = get_logger(__name__)
    logger.info(f"Logging configured for environment: {environment}")


def get_logger(
    name: str, correlation_id: Optional[str] = None
) -> Union[logging.Logger, logging.LoggerAdapter]:
    """
    Get a logger instance with optional correlation ID.

    Args:
        name: Logger name (typically __name__)
        correlation_id: Optional correlation ID for request tracing

    Returns:
        Configured logger instance
    """
    # Ensure logging is configured
    if not _logger_registry:
        setup_logging()

    logger = logging.getLogger(name)

    # Store in registry to prevent garbage collection
    _logger_registry[name] = logger

    # Add correlation ID if provided
    if correlation_id:
        # Use a custom LoggerAdapter to add correlation_id to all records
        class CorrelationAdapter(logging.LoggerAdapter):
            def process(self, msg, kwargs):
                return msg, kwargs

            def _log(
                self, level, msg, args, exc_info=None, extra=None, stack_info=False
            ):
                if extra is None:
                    extra = {}
                extra["correlation_id"] = self.extra["correlation_id"]
                self.logger._log(
                    level,
                    msg,
                    args,
                    exc_info=exc_info,
                    extra=extra,
                    stack_info=stack_info,
                )

        return CorrelationAdapter(logger, {"correlation_id": correlation_id})

    return logger


def set_correlation_id(correlation_id: str) -> None:
    """
    Set correlation ID for the current thread.

    Args:
        correlation_id: Correlation ID to set
    """
    import threading

    setattr(threading.current_thread(), "correlation_id", correlation_id)


def get_correlation_id() -> Optional[str]:
    """
    Get correlation ID for the current thread.

    Returns:
        Current correlation ID or None
    """
    import threading

    return getattr(threading.current_thread(), "correlation_id", None)


# Context manager for correlation tracking
class CorrelationContext:
    """Context manager for correlation ID tracking."""

    def __init__(self, correlation_id: str):
        self.correlation_id = correlation_id
        self.previous_id = None

    def __enter__(self):
        self.previous_id = get_correlation_id()
        set_correlation_id(self.correlation_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.previous_id:
            set_correlation_id(self.previous_id)
        else:
            import threading

            if hasattr(threading.current_thread(), "correlation_id"):
                delattr(threading.current_thread(), "correlation_id")


# Convenience function for creating correlation contexts
def with_correlation(correlation_id: str) -> CorrelationContext:
    """
    Create a correlation context for request tracing.

    Usage:
        with with_correlation('req-123'):
            logger.info("This log will include correlation ID")

    Args:
        correlation_id: Correlation ID to use

    Returns:
        Correlation context manager
    """
    return CorrelationContext(correlation_id)
