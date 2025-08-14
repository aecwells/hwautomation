"""
Validation mixin for HWAutomation web interface.

This module provides ValidationMixin with common validation patterns,
field validation, type checking, format validation, and business rules.
"""

import ipaddress
import re
from typing import Any, Dict, List


class ValidationMixin:
    """
    Mixin providing common validation patterns.

    Features:
    - Field validation
    - Type checking
    - Format validation
    - Business rules
    """

    def validate_required_fields(
        self, data: Dict[str, Any], required_fields: List[str]
    ) -> List[str]:
        """Validate required fields are present."""
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == "":
                missing_fields.append(field)
        return missing_fields

    def validate_field_types(
        self, data: Dict[str, Any], field_types: Dict[str, type]
    ) -> List[str]:
        """Validate field types."""
        invalid_fields = []
        for field, expected_type in field_types.items():
            if field in data and not isinstance(data[field], expected_type):
                invalid_fields.append(f"{field} must be {expected_type.__name__}")
        return invalid_fields

    def validate_string_length(
        self, data: Dict[str, Any], length_rules: Dict[str, Dict[str, int]]
    ) -> List[str]:
        """Validate string field lengths."""
        errors = []
        for field, rules in length_rules.items():
            if field in data and isinstance(data[field], str):
                value = data[field]
                min_length = rules.get("min", 0)
                max_length = rules.get("max", float("inf"))

                if len(value) < min_length:
                    errors.append(f"{field} must be at least {min_length} characters")
                if len(value) > max_length:
                    errors.append(f"{field} must be at most {max_length} characters")

        return errors

    def validate_ip_address(self, ip_string: str) -> bool:
        """Validate IP address format."""
        try:
            ipaddress.ip_address(ip_string)
            return True
        except ValueError:
            return False

    def validate_server_id(self, server_id: str) -> bool:
        """Validate server ID format."""
        # Server IDs should be alphanumeric with hyphens/underscores
        pattern = r"^[a-zA-Z0-9_-]+$"
        return bool(re.match(pattern, server_id))

    def validate_device_type(self, device_type: str) -> bool:
        """Validate device type format."""
        # Device types follow pattern like 'a1.c5.large' or 's2_c2_small'
        patterns = [
            r"^[a-z]\d+\.[c]\d+\.(small|medium|large)$",  # New format
            r"^s\d+_c\d+_(small|medium|large)$",  # Legacy format
        ]
        return any(re.match(pattern, device_type) for pattern in patterns)

    def validate_workflow_status(self, status: str) -> bool:
        """Validate workflow status."""
        valid_statuses = ["PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"]
        return status in valid_statuses

    def validate_email(self, email: str) -> bool:
        """Validate email address format."""
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def validate_url(self, url: str) -> bool:
        """Validate URL format."""
        pattern = r"^https?://[^\s/$.?#].[^\s]*$"
        return bool(re.match(pattern, url))

    def validate_json_structure(
        self, data: Dict[str, Any], required_structure: Dict[str, type]
    ) -> List[str]:
        """Validate JSON data matches expected structure."""
        errors = []

        # Check required fields exist and have correct types
        for field, expected_type in required_structure.items():
            if field not in data:
                errors.append(f"Missing required field: {field}")
            elif not isinstance(data[field], expected_type):
                errors.append(
                    f"Field '{field}' must be {expected_type.__name__}, "
                    f"got {type(data[field]).__name__}"
                )

        return errors

    def validate_range(
        self, value: float, min_val: float = None, max_val: float = None
    ) -> bool:
        """Validate numeric value is within range."""
        if min_val is not None and value < min_val:
            return False
        if max_val is not None and value > max_val:
            return False
        return True

    def validate_enum_value(self, value: str, valid_values: List[str]) -> bool:
        """Validate value is in allowed enumeration."""
        return value in valid_values
