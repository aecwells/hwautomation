"""Unified logging package for HWAutomation.

This package provides basic unified logging functionality for
consistent logging across all HWAutomation modules.

Phase 1 Components:
- get_logger: Get configured logger instances
- setup_logging: Configure logging for the application
- log_activity: Track user and system activities
- get_dashboard_activities: Retrieve recent activities for dashboard
"""

from .activity import (
    get_activity_logger,
    get_dashboard_activities,
    log_activity,
)

# Phase 1 basic logging configuration
from .config import (
    get_correlation_id,
    get_logger,
    set_correlation_id,
    setup_logging,
    with_correlation,
)

__all__ = [
    # Core logging functions
    "get_logger",
    "setup_logging",
    "set_correlation_id",
    "get_correlation_id",
    "with_correlation",
    # Activity tracking
    "log_activity",
    "get_activity_logger",
    "get_dashboard_activities",
]
