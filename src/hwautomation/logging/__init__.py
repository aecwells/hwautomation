"""Unified logging package for HWAutomation.

This package provides comprehensive logging functionality including
basic Python logging, activity tracking for dashboard integration,
and log file management utilities.

Key components:
- get_logger: Get configured logger instances
- log_activity: Track user and system activities
- get_dashboard_activities: Retrieve recent activities for dashboard
"""

from .activity import (
    get_activity_logger,
    get_dashboard_activities,
    log_activity,
)
from .config import (
    get_correlation_id,
    get_logger,
    set_correlation_id,
    setup_logging,
    with_correlation,
)

__all__ = [
    "get_logger",
    "setup_logging",
    "set_correlation_id",
    "get_correlation_id",
    "with_correlation",
    "log_activity",
    "get_activity_logger",
    "get_dashboard_activities",
]
