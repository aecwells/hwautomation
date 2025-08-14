"""
Server data serializers.

This module provides serialization for server-related data including
hardware information, network configuration, and BIOS settings.
"""

import json
from typing import Any, Dict

from .base import BaseSerializer, SerializationMixin


class ServerSerializer(BaseSerializer, SerializationMixin):
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
        timestamp_fields = [
            "created_at",
            "updated_at",
            "commissioned_at",
            "deployed_at",
            "last_seen",
            "last_heartbeat",
        ]
        formatted_data["timestamps"] = self._format_timestamps(
            server_data, timestamp_fields
        )

        return formatted_data

    def _format_server_status(self, status: Any) -> Dict[str, Any]:
        """Format server status information."""
        return self._format_status(status, "unknown")

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


class ServerListSerializer(BaseSerializer):
    """Optimized serializer for server lists with minimal data."""

    def serialize_item(self, item: Any) -> Dict[str, Any]:
        """Serialize server data with minimal fields for lists."""
        data = super().serialize_item(item)

        if isinstance(item, dict):
            server_data = item
        else:
            server_data = data

        return {
            "id": server_data.get("id"),
            "hostname": server_data.get("hostname"),
            "status": server_data.get("status"),
            "device_type": server_data.get("device_type"),
            "ip_address": server_data.get("ip_address"),
            "last_seen": server_data.get("last_seen"),
        }
