"""
Validation result serializers.

This module provides serialization for validation results including
boarding validation, hardware checks, and error reporting.
"""

from typing import Any, Dict, List

from .base import BaseSerializer, SerializationMixin


class ValidationResultSerializer(BaseSerializer, SerializationMixin):
    """
    Serializer for validation results.

    Features:
    - Validation status formatting
    - Error categorization
    - Remediation suggestions
    - Category-based results
    """

    def serialize_item(self, item: Any) -> Dict[str, Any]:
        """Serialize validation result data."""
        data = super().serialize_item(item)

        if isinstance(item, dict):
            validation_data = item
        else:
            validation_data = data

        formatted_data = {}

        # Basic validation information
        formatted_data["id"] = validation_data.get("id")
        formatted_data["device_id"] = validation_data.get("device_id")
        formatted_data["validation_type"] = validation_data.get("validation_type")
        formatted_data["status"] = self._format_validation_status(
            validation_data.get("status")
        )

        # Results by category
        formatted_data["results"] = self._format_validation_results(validation_data)

        # Summary information
        formatted_data["summary"] = self._format_validation_summary(validation_data)

        # Timing information
        timestamp_fields = ["started_at", "completed_at", "created_at"]
        formatted_data["timing"] = self._format_timestamps(
            validation_data, timestamp_fields
        )

        return formatted_data

    def _format_validation_status(self, status: Any) -> Dict[str, Any]:
        """Format validation status."""
        base_status = self._format_status(status, "unknown")

        if isinstance(status, str):
            # Add validation-specific status information
            base_status.update(
                {
                    "is_passed": status in ["PASSED", "SUCCESS", "COMPLETED"],
                    "is_failed": status in ["FAILED", "ERROR"],
                    "is_running": status in ["RUNNING", "IN_PROGRESS", "PENDING"],
                }
            )

        return base_status

    def _format_validation_results(
        self, validation_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Format validation results by category."""
        results_data = validation_data.get("results", [])
        if not isinstance(results_data, list):
            results_data = []

        formatted_results = []
        for result in results_data:
            if isinstance(result, dict):
                formatted_result = {
                    "category": result.get("category"),
                    "name": result.get("name"),
                    "status": result.get("status"),
                    "message": result.get("message"),
                    "details": result.get("details"),
                    "remediation": result.get("remediation"),
                    "severity": result.get("severity", "medium"),
                }

                # Add timing if available
                if result.get("duration"):
                    formatted_result["duration"] = result["duration"]
                    formatted_result["duration_human"] = self._format_duration(
                        result["duration"]
                    )

                formatted_results.append(formatted_result)

        return formatted_results

    def _format_validation_summary(
        self, validation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format validation summary."""
        summary = {
            "total_checks": validation_data.get("total_checks", 0),
            "passed_checks": validation_data.get("passed_checks", 0),
            "failed_checks": validation_data.get("failed_checks", 0),
            "skipped_checks": validation_data.get("skipped_checks", 0),
        }

        # Calculate percentages
        total = summary["total_checks"]
        if total > 0:
            summary["pass_rate"] = (summary["passed_checks"] / total) * 100
            summary["fail_rate"] = (summary["failed_checks"] / total) * 100
        else:
            summary["pass_rate"] = 0
            summary["fail_rate"] = 0

        # Overall status
        if summary["failed_checks"] == 0:
            summary["overall_status"] = "passed"
        elif summary["passed_checks"] == 0:
            summary["overall_status"] = "failed"
        else:
            summary["overall_status"] = "partial"

        return summary


class BoardingValidationSerializer(ValidationResultSerializer):
    """Specialized serializer for boarding validation results."""

    def serialize_item(self, item: Any) -> Dict[str, Any]:
        """Serialize boarding validation with additional boarding-specific data."""
        data = super().serialize_item(item)

        if isinstance(item, dict):
            validation_data = item
        else:
            validation_data = data

        # Add boarding-specific information
        data["boarding_info"] = {
            "device_type": validation_data.get("device_type"),
            "server_ip": validation_data.get("server_ip"),
            "ipmi_ip": validation_data.get("ipmi_ip"),
            "vendor": validation_data.get("vendor"),
            "model": validation_data.get("model"),
        }

        # Add category-specific results
        data["categories"] = self._format_boarding_categories(validation_data)

        return data

    def _format_boarding_categories(
        self, validation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Format boarding validation by category."""
        categories = {}

        category_names = [
            "connectivity",
            "hardware",
            "ipmi",
            "bios",
            "network",
            "configuration",
        ]

        for category in category_names:
            category_data = validation_data.get(f"{category}_validation", {})
            if category_data:
                categories[category] = {
                    "status": category_data.get("status", "unknown"),
                    "message": category_data.get("message", ""),
                    "checks": category_data.get("checks", []),
                    "remediation": category_data.get("remediation"),
                }

        return categories


class ValidationErrorSerializer(BaseSerializer):
    """Serializer for validation errors and failures."""

    def serialize_item(self, item: Any) -> Dict[str, Any]:
        """Serialize validation error data."""
        data = super().serialize_item(item)

        if isinstance(item, dict):
            error_data = item
        else:
            error_data = data

        return {
            "error_code": error_data.get("error_code"),
            "category": error_data.get("category"),
            "severity": error_data.get("severity", "medium"),
            "message": error_data.get("message"),
            "details": error_data.get("details"),
            "remediation": error_data.get("remediation"),
            "context": error_data.get("context", {}),
            "timestamp": error_data.get("timestamp"),
        }
