"""
Device and hardware data serializers.

This module provides serialization for device configuration data
including hardware specifications, BIOS templates, and capabilities.
"""

import json
from typing import Any, Dict

from .base import BaseSerializer, SerializationMixin


class DeviceSerializer(BaseSerializer, SerializationMixin):
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


class HardwareSpecSerializer(BaseSerializer):
    """Simplified serializer for hardware specifications only."""

    def serialize_item(self, item: Any) -> Dict[str, Any]:
        """Serialize hardware specifications with minimal data."""
        data = super().serialize_item(item)

        if isinstance(item, dict):
            device_data = item
        else:
            device_data = data

        return {
            "device_type": device_data.get("device_type"),
            "vendor": device_data.get("vendor"),
            "model": device_data.get("model"),
            "cpu_count": device_data.get("cpu_count"),
            "memory_gb": device_data.get("memory_gb"),
            "storage_capacity_gb": device_data.get("storage_capacity_gb"),
            "network_ports": device_data.get("network_ports"),
        }
