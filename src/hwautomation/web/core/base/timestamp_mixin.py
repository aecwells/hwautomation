"""
Timestamp utilities mixin for HWAutomation web interface.

This module provides TimestampMixin with time handling utilities,
duration calculations, and timestamp formatting functions.
"""

import datetime
import time
from typing import Optional, Union


class TimestampMixin:
    """
    Mixin providing timestamp and time utilities.

    Features:
    - Timestamp formatting
    - Duration calculations
    - Time parsing
    - Human-readable time formats
    """

    @staticmethod
    def current_timestamp() -> float:
        """Get current Unix timestamp."""
        return time.time()

    @staticmethod
    def format_timestamp(
        timestamp: Optional[Union[float, int]] = None,
        format_str: str = "%Y-%m-%d %H:%M:%S",
        utc: bool = False,
    ) -> str:
        """Format timestamp as human-readable string."""
        if timestamp is None:
            timestamp = time.time()

        if utc:
            dt = datetime.datetime.utcfromtimestamp(timestamp)
        else:
            dt = datetime.datetime.fromtimestamp(timestamp)

        if format_str == "iso":
            return dt.isoformat()
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

    @staticmethod
    def time_ago(timestamp: float) -> str:
        """Format timestamp as 'time ago' string."""
        duration = time.time() - timestamp

        if duration < 60:
            return f"{int(duration)} seconds ago"
        elif duration < 3600:
            minutes = int(duration / 60)
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif duration < 86400:
            hours = int(duration / 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = int(duration / 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"

    @staticmethod
    def is_timestamp_recent(timestamp: float, max_age_seconds: int = 300) -> bool:
        """Check if timestamp is within max_age_seconds from now."""
        return time.time() - timestamp <= max_age_seconds

    @staticmethod
    def timestamp_to_date(timestamp: float) -> str:
        """Convert timestamp to date string (YYYY-MM-DD)."""
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d")

    @staticmethod
    def timestamp_to_time(timestamp: float) -> str:
        """Convert timestamp to time string (HH:MM:SS)."""
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%H:%M:%S")

    @staticmethod
    def start_of_day(timestamp: Optional[float] = None) -> float:
        """Get timestamp for start of day (00:00:00)."""
        if timestamp is None:
            timestamp = time.time()

        dt = datetime.datetime.fromtimestamp(timestamp)
        start_of_day = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        return start_of_day.timestamp()

    @staticmethod
    def end_of_day(timestamp: Optional[float] = None) -> float:
        """Get timestamp for end of day (23:59:59)."""
        if timestamp is None:
            timestamp = time.time()

        dt = datetime.datetime.fromtimestamp(timestamp)
        end_of_day = dt.replace(hour=23, minute=59, second=59, microsecond=999999)
        return end_of_day.timestamp()
