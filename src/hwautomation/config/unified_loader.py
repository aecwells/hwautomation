"""
Unified configuration loader for HWAutomation.

This module provides a single interface to load and manage device configurations
from the unified YAML structure while maintaining backward compatibility with
existing BIOS and firmware configuration systems.
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import yaml

from ..logging import get_logger

logger = get_logger(__name__)


@dataclass
class DeviceInfo:
    """Complete device information from unified config."""

    device_type: str
    vendor: str
    motherboard: str
    vendor_info: Dict[str, Any]
    motherboard_info: Dict[str, Any]
    device_config: Dict[str, Any]


@dataclass
class ConfigStats:
    """Configuration statistics."""

    vendors: int
    motherboards: int
    device_types: int
    total_firmware_files: int


class UnifiedConfigLoader:
    """
    Unified configuration loader with backward compatibility.

    This class provides a single interface to load device configurations
    from the unified YAML structure and can provide backward-compatible
    interfaces for existing systems.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the unified configuration loader.

        Args:
            config_path: Path to unified configuration file. If None, uses default.
        """
        self.config_path = config_path or self._get_default_config_path()
        self._config_cache: Optional[Dict[str, Any]] = None
        self._last_modified: Optional[float] = None

        logger.info(f"Initialized UnifiedConfigLoader with: {self.config_path}")

    def _get_default_config_path(self) -> str:
        """Get default unified configuration path."""
        # Look for config relative to this file
        current_dir = Path(__file__).parent
        project_root = current_dir.parent.parent.parent
        config_path = (
            project_root / "configs" / "devices" / "unified_device_config.yaml"
        )

        return str(config_path)

    def _should_reload_config(self) -> bool:
        """Check if configuration should be reloaded."""
        if not os.path.exists(self.config_path):
            return False

        current_modified = os.path.getmtime(self.config_path)
        return (
            self._config_cache is None
            or self._last_modified is None
            or current_modified > self._last_modified
        )

    def _load_config(self, force_reload: bool = False) -> Dict[str, Any]:
        """
        Load and cache the unified configuration.

        Args:
            force_reload: Force reload even if cached

        Returns:
            Dictionary containing the unified configuration

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If config file is invalid YAML
        """
        if not force_reload and not self._should_reload_config():
            return self._config_cache

        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"Unified config file not found: {self.config_path}"
            )

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config_cache = yaml.safe_load(f)
                self._last_modified = os.path.getmtime(self.config_path)

                logger.debug(f"Loaded unified config from: {self.config_path}")
                return self._config_cache

        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in config file {self.config_path}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load config file {self.config_path}: {e}")
            raise

    def reload_config(self) -> None:
        """Force reload of configuration from disk."""
        logger.info("Force reloading unified configuration")
        self._load_config(force_reload=True)

    def get_device_by_type(self, device_type: str) -> Optional[DeviceInfo]:
        """
        Get complete device information by device type.

        Args:
            device_type: Device type identifier (e.g., 'a1.c5.large')

        Returns:
            DeviceInfo object with complete information, or None if not found
        """
        config = self._load_config()

        for vendor_name, vendor_data in config["device_configuration"][
            "vendors"
        ].items():
            for motherboard_name, motherboard_data in vendor_data[
                "motherboards"
            ].items():
                device_types = motherboard_data.get("device_types", {})
                if device_type in device_types:
                    return DeviceInfo(
                        device_type=device_type,
                        vendor=vendor_name,
                        motherboard=motherboard_name,
                        vendor_info=vendor_data,
                        motherboard_info=motherboard_data,
                        device_config=device_types[device_type],
                    )

        logger.warning(f"Device type '{device_type}' not found in configuration")
        return None

    def get_motherboard_info(self, motherboard: str) -> Optional[Dict[str, Any]]:
        """
        Get motherboard information including all device types.

        Args:
            motherboard: Motherboard model name

        Returns:
            Dictionary with motherboard info and device types, or None if not found
        """
        config = self._load_config()

        for vendor_name, vendor_data in config["device_configuration"][
            "vendors"
        ].items():
            motherboards = vendor_data.get("motherboards", {})
            if motherboard in motherboards:
                motherboard_data = motherboards[motherboard]
                return {
                    "motherboard": motherboard,
                    "vendor": vendor_name,
                    "vendor_info": vendor_data,
                    "motherboard_info": motherboard_data,
                    "device_types": list(
                        motherboard_data.get("device_types", {}).keys()
                    ),
                }

        logger.warning(f"Motherboard '{motherboard}' not found in configuration")
        return None

    def get_vendor_info(self, vendor: str) -> Optional[Dict[str, Any]]:
        """
        Get complete vendor information.

        Args:
            vendor: Vendor name

        Returns:
            Dictionary with vendor information, or None if not found
        """
        config = self._load_config()
        vendors = config["device_configuration"]["vendors"]

        if vendor in vendors:
            vendor_data = vendors[vendor]
            return {
                "vendor": vendor,
                "vendor_info": vendor_data,
                "motherboards": list(vendor_data.get("motherboards", {}).keys()),
                "total_device_types": sum(
                    len(mb.get("device_types", {}))
                    for mb in vendor_data.get("motherboards", {}).values()
                ),
            }

        logger.warning(f"Vendor '{vendor}' not found in configuration")
        return None

    def list_all_device_types(self) -> List[str]:
        """
        Get sorted list of all device types in the system.

        Returns:
            Sorted list of device type identifiers
        """
        config = self._load_config()
        device_types = []

        for vendor_data in config["device_configuration"]["vendors"].values():
            for motherboard_data in vendor_data.get("motherboards", {}).values():
                device_types.extend(motherboard_data.get("device_types", {}).keys())

        return sorted(set(device_types))

    def list_vendors(self) -> List[str]:
        """Get list of all vendors."""
        config = self._load_config()
        return list(config["device_configuration"]["vendors"].keys())

    def list_motherboards(self, vendor: Optional[str] = None) -> List[str]:
        """
        Get list of motherboards, optionally filtered by vendor.

        Args:
            vendor: Optional vendor filter

        Returns:
            List of motherboard names
        """
        config = self._load_config()
        motherboards = []

        vendors_to_check = [vendor] if vendor else self.list_vendors()

        for vendor_name in vendors_to_check:
            if vendor_name in config["device_configuration"]["vendors"]:
                vendor_data = config["device_configuration"]["vendors"][vendor_name]
                motherboards.extend(vendor_data.get("motherboards", {}).keys())

        return sorted(set(motherboards))

    def get_stats(self) -> ConfigStats:
        """
        Get configuration statistics.

        Returns:
            ConfigStats object with current statistics
        """
        config = self._load_config()
        vendors = config["device_configuration"]["vendors"]

        total_motherboards = sum(
            len(v.get("motherboards", {})) for v in vendors.values()
        )

        total_device_types = sum(
            len(mb.get("device_types", {}))
            for v in vendors.values()
            for mb in v.get("motherboards", {}).values()
        )

        total_firmware_files = sum(
            len(mb.get("firmware_tracking", {}).get("bios", {}).get("files", []))
            + len(mb.get("firmware_tracking", {}).get("bmc", {}).get("files", []))
            for v in vendors.values()
            for mb in v.get("motherboards", {}).values()
        )

        return ConfigStats(
            vendors=len(vendors),
            motherboards=total_motherboards,
            device_types=total_device_types,
            total_firmware_files=total_firmware_files,
        )

    def validate_device_type(self, device_type: str) -> bool:
        """
        Validate that a device type exists in configuration.

        Args:
            device_type: Device type to validate

        Returns:
            True if device type exists, False otherwise
        """
        return self.get_device_by_type(device_type) is not None

    def get_device_types_by_vendor(self, vendor: str) -> List[str]:
        """
        Get all device types for a specific vendor.

        Args:
            vendor: Vendor name

        Returns:
            List of device types for the vendor
        """
        config = self._load_config()
        device_types = []

        if vendor in config["device_configuration"]["vendors"]:
            vendor_data = config["device_configuration"]["vendors"][vendor]
            for motherboard_data in vendor_data.get("motherboards", {}).values():
                device_types.extend(motherboard_data.get("device_types", {}).keys())

        return sorted(set(device_types))

    def get_device_types_by_motherboard(self, motherboard: str) -> List[str]:
        """
        Get all device types for a specific motherboard.

        Args:
            motherboard: Motherboard model name

        Returns:
            List of device types for the motherboard
        """
        motherboard_info = self.get_motherboard_info(motherboard)
        return motherboard_info["device_types"] if motherboard_info else []

    def search_devices(
        self,
        vendor: Optional[str] = None,
        motherboard: Optional[str] = None,
        cpu_name: Optional[str] = None,
        min_ram_gb: Optional[int] = None,
        max_ram_gb: Optional[int] = None,
    ) -> List[DeviceInfo]:
        """
        Search for devices matching criteria.

        Args:
            vendor: Filter by vendor
            motherboard: Filter by motherboard
            cpu_name: Filter by CPU name (partial match)
            min_ram_gb: Minimum RAM in GB
            max_ram_gb: Maximum RAM in GB

        Returns:
            List of matching DeviceInfo objects
        """
        results = []
        all_device_types = self.list_all_device_types()

        for device_type in all_device_types:
            device_info = self.get_device_by_type(device_type)
            if not device_info:
                continue

            # Apply filters
            if vendor and device_info.vendor != vendor:
                continue

            if motherboard and device_info.motherboard != motherboard:
                continue

            hardware_specs = device_info.device_config.get("hardware_specs", {})

            if (
                cpu_name
                and cpu_name.lower() not in hardware_specs.get("cpu_name", "").lower()
            ):
                continue

            ram_gb = hardware_specs.get("ram_gb", 0)
            if min_ram_gb and ram_gb < min_ram_gb:
                continue

            if max_ram_gb and ram_gb > max_ram_gb:
                continue

            results.append(device_info)

        return results

    def get_global_settings(self) -> Dict[str, Any]:
        """Get global configuration settings."""
        config = self._load_config()
        return config["device_configuration"].get("global_settings", {})

    def get_version(self) -> str:
        """Get configuration version."""
        config = self._load_config()
        return config["device_configuration"].get("version", "unknown")

    def get_last_updated(self) -> str:
        """Get last updated timestamp."""
        config = self._load_config()
        return config["device_configuration"].get("last_updated", "unknown")
