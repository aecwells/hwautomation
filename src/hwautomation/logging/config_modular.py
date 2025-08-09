"""
Modular Logging Configuration for HWAutomation.

This is the new modular configuration system that leverages separate
formatters, handlers, and filters modules for better maintainability.

Features:
- Modular component architecture
- Enhanced configuration management
- Advanced logging profiles
- Dynamic reconfiguration support
"""

import logging
import logging.config
import os
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .filters import (
    ComponentFilter,
    ContextFilter,
    CorrelationFilter,
    EnvironmentFilter,
    LevelRangeFilter,
    RateLimitFilter,
)

# Import our modular components
from .formatters import (
    DashboardFormatter,
    DebugFormatter,
    JSONFormatter,
    MultilineFormatter,
    PerformanceFormatter,
    StructuredFormatter,
)
from .handlers import (
    BufferedHandler,
    CompressedRotatingFileHandler,
    DatabaseHandler,
    MetricsHandler,
    WebSocketHandler,
)

# Global logger registry and configuration state
_logger_registry: Dict[str, logging.Logger] = {}
_current_config: Optional[Dict[str, Any]] = None
_config_lock = threading.Lock()

# Thread-local storage for correlation IDs
_thread_local = threading.local()


class LoggingConfigManager:
    """
    Advanced logging configuration manager with modular component support.

    Features:
    - Profile-based configuration
    - Dynamic handler registration
    - Component hot-swapping
    - Configuration validation
    """

    def __init__(self):
        self.profiles: Dict[str, Dict[str, Any]] = {}
        self.handlers: Dict[str, logging.Handler] = {}
        self.filters: Dict[str, logging.Filter] = {}
        self.formatters: Dict[str, logging.Formatter] = {}
        self._setup_default_profiles()

    def _setup_default_profiles(self):
        """Setup default logging profiles."""

        # Development Profile - Maximum visibility
        self.profiles["development"] = {
            "level": logging.DEBUG,
            "handlers": ["console", "file", "database"],
            "formatters": {
                "console": "debug",
                "file": "detailed",
                "database": "structured",
            },
            "filters": ["correlation", "context"],
            "features": {
                "rate_limiting": False,
                "metrics_collection": True,
                "websocket_streaming": True,
                "multiline_support": True,
            },
        }

        # Staging Profile - Balanced approach
        self.profiles["staging"] = {
            "level": logging.INFO,
            "handlers": ["console", "file", "error_file", "database"],
            "formatters": {
                "console": "structured",
                "file": "structured",
                "error_file": "json",
                "database": "structured",
            },
            "filters": ["correlation", "environment", "rate_limit"],
            "features": {
                "rate_limiting": True,
                "metrics_collection": True,
                "websocket_streaming": True,
                "compression": True,
            },
        }

        # Production Profile - Performance optimized
        self.profiles["production"] = {
            "level": logging.WARNING,
            "handlers": ["console", "compressed_file", "error_file", "metrics"],
            "formatters": {
                "console": "performance",
                "compressed_file": "json",
                "error_file": "json",
                "metrics": "structured",
            },
            "filters": ["correlation", "environment", "rate_limit", "component"],
            "features": {
                "rate_limiting": True,
                "metrics_collection": True,
                "compression": True,
                "buffering": True,
            },
        }

        # Testing Profile - Minimal overhead
        self.profiles["testing"] = {
            "level": logging.CRITICAL,
            "handlers": ["console"],
            "formatters": {"console": "performance"},
            "filters": [],
            "features": {
                "rate_limiting": False,
                "metrics_collection": False,
                "websocket_streaming": False,
            },
        }

    def create_formatters(self) -> Dict[str, logging.Formatter]:
        """Create and return all available formatters."""
        return {
            "structured": StructuredFormatter(
                "%(asctime)s - %(correlation_id)s - %(module_context)s - %(levelname)s - %(message)s"
            ),
            "json": JSONFormatter(),
            "dashboard": DashboardFormatter(
                "%(asctime)s [%(severity_class)s] %(component_name)s: %(truncated_message)s"
            ),
            "debug": DebugFormatter(
                "%(asctime)s [%(correlation_display)s] %(short_filename)s:%(lineno)d %(thread_info)s - %(levelname)s - %(message)s"
            ),
            "performance": PerformanceFormatter(),
            "multiline": MultilineFormatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            ),
            "detailed": StructuredFormatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
            ),
        }

    def create_filters(
        self, profile_config: Dict[str, Any]
    ) -> Dict[str, logging.Filter]:
        """Create and configure logging filters based on profile."""
        filters: Dict[str, logging.Filter] = {}

        if "correlation" in profile_config.get("filters", []):
            filters["correlation"] = CorrelationFilter()

        if "context" in profile_config.get("filters", []):
            filters["context"] = ContextFilter()

        if "environment" in profile_config.get("filters", []):
            environment = os.getenv("HW_AUTOMATION_ENV", "development")
            filters["environment"] = EnvironmentFilter(environment)

        if "rate_limit" in profile_config.get("filters", []):
            filters["rate_limit"] = RateLimitFilter(
                max_rate=10.0, window_size=60.0, burst_size=20
            )

        if "component" in profile_config.get("filters", []):
            # Production component filtering - exclude noisy components
            filters["component"] = ComponentFilter(
                exclude_patterns={"hwautomation.web.static", "urllib3.connectionpool"}
            )

        return filters

    def create_handlers(
        self, profile_config: Dict[str, Any]
    ) -> Dict[str, logging.Handler]:
        """Create handlers based on profile configuration."""
        handlers: Dict[str, logging.Handler] = {}
        formatters = self.create_formatters()
        filters = self.create_filters(profile_config)

        # Ensure logs directory exists
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)

        handler_configs = profile_config.get("handlers", [])
        formatter_mapping = profile_config.get("formatters", {})

        if "console" in handler_configs:
            handler: logging.Handler = logging.StreamHandler()
            handler.setFormatter(
                formatters.get(formatter_mapping.get("console", "structured"))
            )
            self._add_filters_to_handler(handler, filters, profile_config)
            handlers["console"] = handler

        if "file" in handler_configs:
            handler = logging.handlers.RotatingFileHandler(
                "logs/hwautomation.log", maxBytes=10485760, backupCount=5  # 10MB
            )
            handler.setFormatter(
                formatters.get(formatter_mapping.get("file", "structured"))
            )
            self._add_filters_to_handler(handler, filters, profile_config)
            handlers["file"] = handler

        if "compressed_file" in handler_configs:
            handler = CompressedRotatingFileHandler(
                "logs/hwautomation.log",
                maxBytes=52428800,  # 50MB
                backupCount=10,
                compress_level=6,
            )
            handler.setFormatter(
                formatters.get(formatter_mapping.get("compressed_file", "json"))
            )
            self._add_filters_to_handler(handler, filters, profile_config)

            # Wrap with buffered handler if buffering is enabled
            if profile_config.get("features", {}).get("buffering", False):
                handlers["compressed_file"] = BufferedHandler(handler, buffer_size=1000)
            else:
                handlers["compressed_file"] = handler

        if "error_file" in handler_configs:
            handler = CompressedRotatingFileHandler(
                "logs/errors.log",
                maxBytes=10485760,  # 10MB
                backupCount=20,
                compress_level=9,
            )
            handler.setLevel(logging.ERROR)
            handler.setFormatter(
                formatters.get(formatter_mapping.get("error_file", "json"))
            )
            self._add_filters_to_handler(handler, filters, profile_config)
            handlers["error_file"] = handler

        if "database" in handler_configs:
            handler = DatabaseHandler("logs/logging.db", max_records=50000)
            handler.setFormatter(
                formatters.get(formatter_mapping.get("database", "structured"))
            )
            self._add_filters_to_handler(handler, filters, profile_config)
            handlers["database"] = handler

        if "websocket" in handler_configs:
            handler = WebSocketHandler()
            handler.setFormatter(formatters.get("dashboard"))
            self._add_filters_to_handler(handler, filters, profile_config)
            handlers["websocket"] = handler

        if "metrics" in handler_configs:
            handler = MetricsHandler()
            handler.setFormatter(
                formatters.get(formatter_mapping.get("metrics", "structured"))
            )
            handlers["metrics"] = handler

        return handlers

    def _add_filters_to_handler(
        self,
        handler: logging.Handler,
        filters: Dict[str, logging.Filter],
        profile_config: Dict[str, Any],
    ):
        """Add appropriate filters to a handler."""
        filter_names = profile_config.get("filters", [])
        for filter_name in filter_names:
            if filter_name in filters:
                handler.addFilter(filters[filter_name])

    def apply_profile(self, profile_name: str, **overrides) -> Dict[str, Any]:
        """Apply a logging profile with optional overrides."""
        if profile_name not in self.profiles:
            raise ValueError(f"Unknown profile: {profile_name}")

        profile_config = self.profiles[profile_name].copy()

        # Apply overrides
        for key, value in overrides.items():
            if key in profile_config:
                if isinstance(profile_config[key], dict) and isinstance(value, dict):
                    profile_config[key].update(value)
                else:
                    profile_config[key] = value

        # Create logging configuration
        handlers = self.create_handlers(profile_config)

        # Store handlers for later access
        self.handlers.update(handlers)

        # Build logging config dict
        config = {
            "version": 1,
            "disable_existing_loggers": False,
            "handlers": {
                name: {
                    "class": handler.__class__.__module__
                    + "."
                    + handler.__class__.__name__,
                    "level": getattr(handler, "level", logging.NOTSET),
                }
                for name, handler in handlers.items()
            },
            "loggers": {
                "hwautomation": {
                    "level": profile_config["level"],
                    "handlers": list(handlers.keys()),
                    "propagate": False,
                }
            },
            "root": {
                "level": logging.WARNING,
                "handlers": ["console"] if "console" in handlers else [],
            },
        }

        return config


# Global configuration manager instance
_config_manager = LoggingConfigManager()


def setup_logging(
    profile: str = None,
    environment: Optional[str] = None,
    force_reload: bool = False,
    **profile_overrides,
) -> None:
    """
    Set up modular logging configuration.

    Args:
        profile: Logging profile name (auto-detected from environment if None)
        environment: Environment name (for profile selection)
        force_reload: Force reload even if already configured
        **profile_overrides: Profile configuration overrides
    """
    global _current_config

    with _config_lock:
        # Don't reconfigure unless forced
        if _logger_registry and not force_reload:
            return

        # Auto-detect profile from environment
        if profile is None:
            environment = environment or os.getenv("HW_AUTOMATION_ENV", "development")
            profile = environment

        # Apply the profile
        try:
            config = _config_manager.apply_profile(
                profile or "development", **profile_overrides
            )
            _current_config = config

            # Configure Python logging with our handlers
            # Note: We manually configure because our handlers are instances
            root_logger = logging.getLogger()

            # Clear existing handlers
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

            # Configure hwautomation logger
            hw_logger = logging.getLogger("hwautomation")
            hw_logger.setLevel(config["loggers"]["hwautomation"]["level"])
            hw_logger.propagate = False

            # Clear existing handlers
            for handler in hw_logger.handlers[:]:
                hw_logger.removeHandler(handler)

            # Add our configured handlers
            for handler_name in config["loggers"]["hwautomation"]["handlers"]:
                if handler_name in _config_manager.handlers:
                    hw_logger.addHandler(_config_manager.handlers[handler_name])

            # Configure root logger
            root_logger.setLevel(config["root"]["level"])
            for handler_name in config["root"]["handlers"]:
                if handler_name in _config_manager.handlers:
                    root_logger.addHandler(_config_manager.handlers[handler_name])

            # Store reference to prevent garbage collection
            _logger_registry["root"] = root_logger
            _logger_registry["hwautomation"] = hw_logger

            # Log successful configuration
            logger = get_logger(__name__)
            logger.info(f"Modular logging configured with profile: {profile}")

        except Exception as e:
            # Fallback to basic configuration
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to configure logging profile '{profile}': {e}")
            logger.info("Using fallback basic configuration")


def get_logger(
    name: str, correlation_id: Optional[str] = None
) -> Union[logging.Logger, logging.LoggerAdapter]:
    """
    Get a configured logger instance with optional correlation ID.

    Args:
        name: Logger name (usually __name__)
        correlation_id: Optional correlation ID for request tracing

    Returns:
        Configured logger or logger adapter with correlation ID
    """
    # Ensure logging is configured
    if not _logger_registry:
        setup_logging()

    logger = logging.getLogger(name)

    if correlation_id:
        return logging.LoggerAdapter(logger, {"correlation_id": correlation_id})

    return logger


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID for current thread."""
    _thread_local.correlation_id = correlation_id

    # Also set on correlation filter if available
    if "correlation" in _config_manager.filters:
        filter_obj = _config_manager.filters["correlation"]
        if hasattr(filter_obj, "set_correlation_id"):
            filter_obj.set_correlation_id(correlation_id)  # type: ignore


def get_correlation_id() -> Optional[str]:
    """Get correlation ID for current thread."""
    correlation_id = getattr(_thread_local, "correlation_id", None)
    if not correlation_id and "correlation" in _config_manager.filters:
        filter_obj = _config_manager.filters["correlation"]
        if hasattr(filter_obj, "get_correlation_id"):
            correlation_id = filter_obj.get_correlation_id()  # type: ignore
    return correlation_id


def clear_correlation_id() -> None:
    """Clear correlation ID for current thread."""
    if hasattr(_thread_local, "correlation_id"):
        delattr(_thread_local, "correlation_id")

    if "correlation" in _config_manager.filters:
        filter_obj = _config_manager.filters["correlation"]
        if hasattr(filter_obj, "clear_correlation_id"):
            filter_obj.clear_correlation_id()  # type: ignore


@contextmanager
def with_correlation(correlation_id: str):
    """Context manager for correlation ID."""
    old_id = get_correlation_id()
    set_correlation_id(correlation_id)
    try:
        yield
    finally:
        if old_id:
            set_correlation_id(old_id)
        else:
            clear_correlation_id()


def add_websocket_manager(manager):
    """Add WebSocket manager to WebSocket handler."""
    if "websocket" in _config_manager.handlers:
        _config_manager.handlers["websocket"].set_websocket_manager(manager)


def get_metrics_handler() -> Optional[MetricsHandler]:
    """Get the metrics handler if configured."""
    handler = _config_manager.handlers.get("metrics")
    if (
        handler
        and hasattr(handler, "__class__")
        and "MetricsHandler" in str(handler.__class__)
    ):
        return handler  # type: ignore
    return None


def reconfigure_logging(profile: str, **profile_overrides) -> None:
    """Reconfigure logging with a different profile."""
    setup_logging(profile=profile, force_reload=True, **profile_overrides)


def get_logging_status() -> Dict[str, Any]:
    """Get current logging configuration status."""
    return {
        "configured": bool(_logger_registry),
        "profile": "unknown",  # Would need to track this
        "handlers": list(_config_manager.handlers.keys()),
        "filters": list(_config_manager.filters.keys()),
        "correlation_id": get_correlation_id(),
        "available_profiles": list(_config_manager.profiles.keys()),
    }
