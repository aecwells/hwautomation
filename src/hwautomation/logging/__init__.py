"""Unified logging package for HWAutomation.

This package provides comprehensive logging functionality including
basic Python logging, activity tracking for dashboard integration,
and advanced modular logging infrastructure.

Key components:
- get_logger: Get configured logger instances
- log_activity: Track user and system activities
- get_dashboard_activities: Retrieve recent activities for dashboard

Modular Components (Phase 4):
- formatters: Custom log formatters (JSON, structured, dashboard, etc.)
- handlers: Advanced handlers (database, websocket, metrics, etc.)
- filters: Log filters (correlation, rate limiting, environment, etc.)
- monitoring: Log aggregation and analysis tools
- config_modular: New modular configuration system
"""

# Export formatters, handlers, filters for advanced usage
from . import filters, formatters, handlers, monitoring
from .activity import (
    get_activity_logger,
    get_dashboard_activities,
    log_activity,
)

# Legacy configuration (Phase 1-3 compatibility)
from .config import (
    get_correlation_id,
    get_logger,
    set_correlation_id,
    setup_logging,
    with_correlation,
)

# New modular components (Phase 4)
from .config_modular import (
    LoggingConfigManager,
    add_websocket_manager,
    get_logging_status,
    get_metrics_handler,
    reconfigure_logging,
)

__all__ = [
    # Core logging functions (backward compatible)
    "get_logger",
    "setup_logging",
    "set_correlation_id",
    "get_correlation_id",
    "with_correlation",
    # Activity tracking
    "log_activity",
    "get_activity_logger",
    "get_dashboard_activities",
    # Advanced modular components
    "LoggingConfigManager",
    "add_websocket_manager",
    "get_logging_status",
    "get_metrics_handler",
    "reconfigure_logging",
    # Component modules
    "formatters",
    "handlers",
    "filters",
    "monitoring",
]
