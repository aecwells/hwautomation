"""
Base serializer classes and common functionality.

This module provides the foundational serialization infrastructure
used by all entity-specific serializers.
"""

import datetime
from typing import Any, Dict, List, Optional

from hwautomation.logging import get_logger

logger = get_logger(__name__)


class BaseSerializer:
    """
    Base serializer with common functionality.

    Features:
    - Field selection
    - Type conversion
    - Validation
    - Nested serialization
    """

    def __init__(
        self,
        fields: Optional[List[str]] = None,
        exclude_fields: Optional[List[str]] = None,
    ):
        self.fields = fields
        self.exclude_fields = exclude_fields or []

    def serialize(self, data: Any) -> Any:
        """Serialize data based on type."""
        if isinstance(data, list):
            return [self.serialize_item(item) for item in data]
        elif isinstance(data, dict):
            return self.serialize_item(data)
        else:
            return self.serialize_item(data)

    def serialize_item(self, item: Any) -> Dict[str, Any]:
        """Serialize a single item."""
        if hasattr(item, "__dict__"):
            # Object with attributes
            data = {}
            for key, value in item.__dict__.items():
                if not key.startswith("_"):  # Skip private attributes
                    data[key] = self._serialize_value(value)
        elif isinstance(item, dict):
            # Dictionary
            data = {key: self._serialize_value(value) for key, value in item.items()}
        else:
            # Primitive value
            return self._serialize_value(item)

        # Apply field filtering
        if self.fields:
            data = {key: value for key, value in data.items() if key in self.fields}

        if self.exclude_fields:
            data = {
                key: value
                for key, value in data.items()
                if key not in self.exclude_fields
            }

        return data

    def _serialize_value(self, value: Any) -> Any:
        """Serialize individual values with type conversion."""
        if value is None:
            return None
        elif isinstance(value, (str, int, float, bool)):
            return value
        elif isinstance(value, datetime.datetime):
            return value.isoformat()
        elif isinstance(value, datetime.date):
            return value.isoformat()
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {key: self._serialize_value(val) for key, val in value.items()}
        elif hasattr(value, "__dict__"):
            return self.serialize_item(value)
        else:
            # Fallback to string representation
            return str(value)


class SerializationMixin:
    """Mixin providing common serialization utilities."""

    @staticmethod
    def _format_status(status: Any, default_name: str = "unknown") -> Dict[str, Any]:
        """Format status information consistently."""
        if not status:
            return {"name": default_name, "description": f"Status {default_name}"}

        if isinstance(status, str):
            return {"name": status, "description": status.replace("_", " ").title()}

        return {
            "name": status.get("name", default_name),
            "description": status.get("description", ""),
            "code": status.get("code"),
            "category": status.get("category"),
        }

    @staticmethod
    def _format_timestamps(
        data: Dict[str, Any], field_names: List[str]
    ) -> Dict[str, Any]:
        """Format timestamp fields consistently."""
        timestamps = {}

        for field in field_names:
            if field in data and data[field]:
                value = data[field]
                if isinstance(value, (int, float)):
                    timestamps[field] = {
                        "timestamp": value,
                        "iso": datetime.datetime.fromtimestamp(value).isoformat(),
                        "human": datetime.datetime.fromtimestamp(value).strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
                    }
                elif isinstance(value, str):
                    timestamps[field] = {"iso": value, "human": value}

        return timestamps

    @staticmethod
    def _format_duration(duration: float) -> str:
        """Format duration in human-readable format."""
        if duration < 60:
            return f"{duration:.1f}s"
        elif duration < 3600:
            minutes = duration / 60
            return f"{minutes:.1f}m"
        else:
            hours = duration / 3600
            return f"{hours:.1f}h"
