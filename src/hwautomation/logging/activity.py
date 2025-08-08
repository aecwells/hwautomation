"""
Real-time Activity Logging System for HWAutomation Dashboard.

Provides a centralized activity feed that captures important system events
and makes them available for real-time display on the dashboard.
"""

import logging
import threading
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

# Get logger directly to avoid circular import
logger = logging.getLogger(__name__)


@dataclass
class ActivityEntry:
    """Represents a single activity log entry."""

    timestamp: str
    level: str
    component: str
    action: str
    message: str
    details: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None


class ActivityLogger:
    """
    Centralized activity logger for capturing and displaying system events.

    This logger captures high-level activities (like workflow starts, device discoveries,
    configuration changes) and makes them available for real-time dashboard display.
    """

    def __init__(self, max_entries: int = 500):
        """
        Initialize the activity logger.

        Args:
            max_entries: Maximum number of activity entries to keep in memory
        """
        self.max_entries = max_entries
        self.activities: deque[ActivityEntry] = deque(maxlen=max_entries)
        self._lock = threading.Lock()

    def log_activity(
        self,
        component: str,
        action: str,
        message: str,
        level: str = "INFO",
        details: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
    ) -> None:
        """
        Log a new activity entry.

        Args:
            component: Component name (e.g., 'workflow', 'maas', 'bios', 'database')
            action: Action being performed (e.g., 'start', 'complete', 'discover', 'configure')
            message: Human-readable message describing the activity
            level: Log level (INFO, WARNING, ERROR, SUCCESS)
            details: Optional additional details
            correlation_id: Optional correlation ID for request tracing
        """
        entry = ActivityEntry(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            level=level,
            component=component,
            action=action,
            message=message,
            details=details or {},
            correlation_id=correlation_id,
        )

        with self._lock:
            self.activities.appendleft(entry)

        # Also log to the standard logging system
        logger.info(
            f"{component}.{action}: {message}",
            extra={
                "correlation_id": correlation_id,
                "component": component,
                "action": action,
                "details": details,
            },
        )

    def get_recent_activities(
        self, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent activities as a list of dictionaries.

        Args:
            limit: Maximum number of activities to return

        Returns:
            List of activity dictionaries
        """
        with self._lock:
            activities = list(self.activities)

        if limit:
            activities = activities[:limit]

        return [asdict(activity) for activity in activities]

    def get_activities_by_component(
        self, component: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get activities filtered by component.

        Args:
            component: Component to filter by
            limit: Maximum number of activities to return

        Returns:
            List of activity dictionaries
        """
        with self._lock:
            filtered = [
                activity
                for activity in self.activities
                if activity.component == component
            ]

        if limit:
            filtered = filtered[:limit]

        return [asdict(activity) for activity in filtered]

    def clear_activities(self) -> None:
        """Clear all stored activities."""
        with self._lock:
            self.activities.clear()
        logger.info("Activity log cleared")


# Global activity logger instance
_activity_logger = None


def get_activity_logger() -> ActivityLogger:
    """Get the global activity logger instance."""
    global _activity_logger
    if _activity_logger is None:
        _activity_logger = ActivityLogger()
    return _activity_logger


def log_activity(
    component: str,
    action: str,
    message: str,
    level: str = "INFO",
    details: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
) -> None:
    """
    Convenience function to log an activity.

    Args:
        component: Component name
        action: Action being performed
        message: Human-readable message
        level: Log level
        details: Optional additional details
        correlation_id: Optional correlation ID
    """
    activity_logger = get_activity_logger()
    activity_logger.log_activity(
        component, action, message, level, details, correlation_id
    )


def get_dashboard_activities(limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get activities formatted for dashboard display.

    Args:
        limit: Maximum number of activities to return

    Returns:
        List of activity dictionaries
    """
    activity_logger = get_activity_logger()
    return activity_logger.get_recent_activities(limit)
