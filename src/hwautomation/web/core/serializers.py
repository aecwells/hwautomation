"""
Serializers for HWAutomation Web Interface.

This module provides standardized data serialization and formatting
for API responses and database models.
"""

import datetime
import json
import time
from typing import Any, Dict, List, Optional, Union

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


class ServerSerializer(BaseSerializer):
    """
    Serializer for server data with specific formatting.

    Features:
    - Server status formatting
    - Hardware information
    - Network configuration
    - BIOS settings
    """

    def serialize_item(self, item: Any) -> Dict[str, Any]:
        """Serialize server data with specific formatting."""
        data = super().serialize_item(item)

        # Format server-specific fields
        if isinstance(item, dict):
            server_data = item
        else:
            server_data = data

        formatted_data = {}

        # Basic server information
        formatted_data["id"] = server_data.get("id")
        formatted_data["hostname"] = server_data.get("hostname")
        formatted_data["status"] = self._format_server_status(server_data.get("status"))

        # Hardware information
        formatted_data["hardware"] = self._format_hardware_info(server_data)

        # Network configuration
        formatted_data["network"] = self._format_network_info(server_data)

        # BIOS configuration
        formatted_data["bios"] = self._format_bios_info(server_data)

        # Timestamps
        formatted_data["timestamps"] = self._format_timestamps(server_data)

        return formatted_data

    def _format_server_status(self, status: Any) -> Dict[str, Any]:
        """Format server status information."""
        if not status:
            return {"name": "unknown", "description": "Status unknown"}

        if isinstance(status, str):
            return {"name": status, "description": status.replace("_", " ").title()}

        return {
            "name": status.get("name", "unknown"),
            "description": status.get("description", ""),
            "code": status.get("code"),
            "category": status.get("category"),
        }

    def _format_hardware_info(self, server_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format hardware information."""
        hardware = {}

        # CPU information
        if "cpu_count" in server_data or "cpu_model" in server_data:
            hardware["cpu"] = {
                "count": server_data.get("cpu_count"),
                "model": server_data.get("cpu_model"),
                "cores": server_data.get("cpu_cores"),
                "threads": server_data.get("cpu_threads"),
            }

        # Memory information
        if "memory_gb" in server_data:
            hardware["memory"] = {
                "total_gb": server_data.get("memory_gb"),
                "modules": server_data.get("memory_modules"),
                "speed": server_data.get("memory_speed"),
            }

        # Storage information
        if "storage_type" in server_data or "storage_capacity_gb" in server_data:
            hardware["storage"] = {
                "type": server_data.get("storage_type"),
                "capacity_gb": server_data.get("storage_capacity_gb"),
                "drives": server_data.get("storage_drives"),
            }

        # Device type and vendor
        hardware["device_type"] = server_data.get("device_type")
        hardware["vendor"] = server_data.get("vendor")
        hardware["model"] = server_data.get("model")

        return hardware

    def _format_network_info(self, server_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format network configuration."""
        network = {}

        # IP addresses
        if "ip_address" in server_data:
            network["ip_address"] = server_data.get("ip_address")

        if "ipmi_ip" in server_data:
            network["ipmi_ip"] = server_data.get("ipmi_ip")

        if "gateway" in server_data:
            network["gateway"] = server_data.get("gateway")

        # Network interfaces
        if "network_interfaces" in server_data:
            network["interfaces"] = server_data.get("network_interfaces")

        # MAC addresses
        if "mac_address" in server_data:
            network["mac_address"] = server_data.get("mac_address")

        return network

    def _format_bios_info(self, server_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format BIOS configuration."""
        bios = {}

        # BIOS version and settings
        bios["version"] = server_data.get("bios_version")
        bios["configured"] = server_data.get("bios_configured", False)
        bios["last_config_time"] = server_data.get("bios_last_config_time")

        # BIOS settings if available
        if "bios_settings" in server_data:
            settings = server_data["bios_settings"]
            if isinstance(settings, str):
                try:
                    bios["settings"] = json.loads(settings)
                except json.JSONDecodeError:
                    bios["settings"] = {}
            else:
                bios["settings"] = settings

        return bios

    def _format_timestamps(self, server_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format timestamp information."""
        timestamps = {}

        # Common timestamp fields
        timestamp_fields = [
            "created_at",
            "updated_at",
            "commissioned_at",
            "deployed_at",
            "last_seen",
            "last_heartbeat",
        ]

        for field in timestamp_fields:
            if field in server_data and server_data[field]:
                value = server_data[field]
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


class WorkflowSerializer(BaseSerializer):
    """
    Serializer for workflow data with progress tracking.

    Features:
    - Workflow status formatting
    - Progress calculation
    - Step information
    - Duration tracking
    """

    def serialize_item(self, item: Any) -> Dict[str, Any]:
        """Serialize workflow data with specific formatting."""
        data = super().serialize_item(item)

        if isinstance(item, dict):
            workflow_data = item
        else:
            workflow_data = data

        formatted_data = {}

        # Basic workflow information
        formatted_data["id"] = workflow_data.get("id")
        formatted_data["type"] = workflow_data.get("type", "unknown")
        formatted_data["server_id"] = workflow_data.get("server_id")
        formatted_data["status"] = self._format_workflow_status(
            workflow_data.get("status")
        )

        # Progress information
        formatted_data["progress"] = self._format_progress_info(workflow_data)

        # Steps information
        formatted_data["steps"] = self._format_steps_info(workflow_data)

        # Timing information
        formatted_data["timing"] = self._format_timing_info(workflow_data)

        # Error information if applicable
        if workflow_data.get("error_message"):
            formatted_data["error"] = {
                "message": workflow_data.get("error_message"),
                "code": workflow_data.get("error_code"),
                "details": workflow_data.get("error_details"),
            }

        return formatted_data

    def _format_workflow_status(self, status: Any) -> Dict[str, Any]:
        """Format workflow status."""
        if isinstance(status, str):
            return {
                "name": status,
                "description": status.replace("_", " ").title(),
                "is_terminal": status in ["COMPLETED", "FAILED", "CANCELLED"],
                "is_active": status in ["PENDING", "RUNNING"],
            }

        return {
            "name": "unknown",
            "description": "Unknown status",
            "is_terminal": False,
            "is_active": False,
        }

    def _format_progress_info(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format progress information."""
        progress = {
            "percentage": workflow_data.get("progress_percentage", 0),
            "current_step": workflow_data.get("current_step"),
            "total_steps": workflow_data.get("total_steps"),
            "message": workflow_data.get("progress_message", ""),
        }

        # Calculate step progress if available
        if progress["current_step"] and progress["total_steps"]:
            try:
                current = int(progress["current_step"])
                total = int(progress["total_steps"])
                step_progress = (current / total) * 100
                progress["step_percentage"] = min(100, max(0, step_progress))
            except (ValueError, ZeroDivisionError):
                progress["step_percentage"] = 0

        return progress

    def _format_steps_info(self, workflow_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Format workflow steps information."""
        steps_data = workflow_data.get("steps", [])
        if isinstance(steps_data, str):
            try:
                steps_data = json.loads(steps_data)
            except json.JSONDecodeError:
                steps_data = []

        formatted_steps = []
        for step in steps_data:
            if isinstance(step, dict):
                formatted_step = {
                    "name": step.get("name"),
                    "status": step.get("status", "pending"),
                    "message": step.get("message", ""),
                    "started_at": step.get("started_at"),
                    "completed_at": step.get("completed_at"),
                    "error": step.get("error"),
                }

                # Calculate step duration
                if step.get("started_at") and step.get("completed_at"):
                    try:
                        start = float(step["started_at"])
                        end = float(step["completed_at"])
                        formatted_step["duration"] = end - start
                    except (ValueError, TypeError):
                        formatted_step["duration"] = None

                formatted_steps.append(formatted_step)

        return formatted_steps

    def _format_timing_info(self, workflow_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format timing information."""
        timing = {}

        # Start and end times
        if workflow_data.get("started_at"):
            timing["started_at"] = workflow_data["started_at"]

        if workflow_data.get("completed_at"):
            timing["completed_at"] = workflow_data["completed_at"]

        # Calculate duration
        if timing.get("started_at") and timing.get("completed_at"):
            try:
                start = float(timing["started_at"])
                end = float(timing["completed_at"])
                timing["duration"] = end - start
                timing["duration_human"] = self._format_duration(timing["duration"])
            except (ValueError, TypeError):
                timing["duration"] = None

        # Estimated completion time for running workflows
        if (
            workflow_data.get("status") == "RUNNING"
            and timing.get("started_at")
            and workflow_data.get("progress_percentage")
        ):
            try:
                start = float(timing["started_at"])
                current = time.time()
                elapsed = current - start
                progress = float(workflow_data["progress_percentage"])

                if progress > 0:
                    estimated_total = elapsed / (progress / 100)
                    estimated_remaining = estimated_total - elapsed
                    timing["estimated_completion"] = current + estimated_remaining
                    timing["estimated_remaining"] = estimated_remaining
                    timing["estimated_remaining_human"] = self._format_duration(
                        estimated_remaining
                    )
            except (ValueError, TypeError, ZeroDivisionError):
                pass

        return timing

    def _format_duration(self, duration: float) -> str:
        """Format duration in human-readable format."""
        if duration < 60:
            return f"{duration:.1f}s"
        elif duration < 3600:
            minutes = duration / 60
            return f"{minutes:.1f}m"
        else:
            hours = duration / 3600
            return f"{hours:.1f}h"


class DeviceSerializer(BaseSerializer):
    """
    Serializer for device/hardware configuration data.

    Features:
    - Device type information
    - Hardware specifications
    - BIOS configuration templates
    - Capability information
    """

    def serialize_item(self, item: Any) -> Dict[str, Any]:
        """Serialize device data with specific formatting."""
        data = super().serialize_item(item)

        if isinstance(item, dict):
            device_data = item
        else:
            device_data = data

        formatted_data = {}

        # Device identification
        formatted_data["device_type"] = device_data.get("device_type")
        formatted_data["vendor"] = device_data.get("vendor")
        formatted_data["model"] = device_data.get("model")
        formatted_data["category"] = device_data.get("category")

        # Hardware specifications
        formatted_data["specifications"] = self._format_specifications(device_data)

        # BIOS configuration
        formatted_data["bios_config"] = self._format_bios_config(device_data)

        # Capabilities and features
        formatted_data["capabilities"] = self._format_capabilities(device_data)

        return formatted_data

    def _format_specifications(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format hardware specifications."""
        specs = {}

        # CPU specifications
        cpu_fields = ["cpu_count", "cpu_model", "cpu_cores", "cpu_threads", "cpu_speed"]
        cpu_spec = {
            field.replace("cpu_", ""): device_data.get(field)
            for field in cpu_fields
            if device_data.get(field)
        }
        if cpu_spec:
            specs["cpu"] = cpu_spec

        # Memory specifications
        memory_fields = ["memory_gb", "memory_modules", "memory_speed", "memory_type"]
        memory_spec = {
            field.replace("memory_", ""): device_data.get(field)
            for field in memory_fields
            if device_data.get(field)
        }
        if memory_spec:
            specs["memory"] = memory_spec

        # Storage specifications
        storage_fields = ["storage_type", "storage_capacity_gb", "storage_drives"]
        storage_spec = {
            field.replace("storage_", ""): device_data.get(field)
            for field in storage_fields
            if device_data.get(field)
        }
        if storage_spec:
            specs["storage"] = storage_spec

        # Network specifications
        network_fields = ["network_ports", "network_speed", "network_type"]
        network_spec = {
            field.replace("network_", ""): device_data.get(field)
            for field in network_fields
            if device_data.get(field)
        }
        if network_spec:
            specs["network"] = network_spec

        return specs

    def _format_bios_config(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format BIOS configuration information."""
        bios_config = {}

        # Template information
        bios_config["template"] = device_data.get("bios_template")
        bios_config["vendor_tool"] = device_data.get("vendor_tool")

        # Configuration settings
        if "bios_settings" in device_data:
            settings = device_data["bios_settings"]
            if isinstance(settings, str):
                try:
                    bios_config["settings"] = json.loads(settings)
                except json.JSONDecodeError:
                    bios_config["settings"] = {}
            else:
                bios_config["settings"] = settings

        # Supported features
        bios_config["supports_redfish"] = device_data.get("supports_redfish", False)
        bios_config["supports_ipmi"] = device_data.get("supports_ipmi", True)

        return bios_config

    def _format_capabilities(self, device_data: Dict[str, Any]) -> Dict[str, Any]:
        """Format device capabilities."""
        capabilities = {}

        # Hardware features
        capabilities["virtualization"] = device_data.get(
            "supports_virtualization", False
        )
        capabilities["uefi_boot"] = device_data.get("supports_uefi", True)
        capabilities["secure_boot"] = device_data.get("supports_secure_boot", False)
        capabilities["tpm"] = device_data.get("has_tpm", False)

        # Management features
        capabilities["remote_management"] = device_data.get(
            "supports_remote_mgmt", True
        )
        capabilities["power_management"] = device_data.get("supports_power_mgmt", True)
        capabilities["firmware_update"] = device_data.get(
            "supports_firmware_update", False
        )

        return capabilities


class APIResponseSerializer:
    """
    Serializer for complete API responses with metadata.

    Features:
    - Response envelope
    - Metadata inclusion
    - Error formatting
    - Pagination support
    """

    @staticmethod
    def success_response(
        data: Any = None,
        message: str = "Success",
        serializer: Optional[BaseSerializer] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create standardized success response."""
        response = {"success": True, "message": message, "timestamp": time.time()}

        if data is not None:
            if serializer:
                response["data"] = serializer.serialize(data)
            else:
                response["data"] = data

        if metadata:
            response["metadata"] = metadata

        return response

    @staticmethod
    def error_response(
        message: str,
        error_code: str,
        details: Optional[str] = None,
        validation_errors: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create standardized error response."""
        response = {
            "success": False,
            "error": message,
            "error_code": error_code,
            "timestamp": time.time(),
        }

        if details:
            response["details"] = details

        if validation_errors:
            response["validation_errors"] = validation_errors

        return response

    @staticmethod
    def paginated_response(
        items: List[Any],
        pagination_info: Dict[str, Any],
        serializer: Optional[BaseSerializer] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create paginated response."""
        if serializer:
            serialized_items = serializer.serialize(items)
        else:
            serialized_items = items

        response = {
            "success": True,
            "data": serialized_items,
            "pagination": pagination_info,
            "timestamp": time.time(),
        }

        if metadata:
            response["metadata"] = metadata

        return response
