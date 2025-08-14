"""
Base BIOS manager classes and interfaces.

This module provides the foundational infrastructure for BIOS management
including abstract base classes and common functionality.
"""

import os
import tempfile
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

from ....logging import get_logger
from ..base import (
    BaseBiosManager,
    BaseDeviceHandler,
    BiosConfigResult,
    ConfigMethod,
    DeviceConfig,
    MethodSelectionResult,
    OperationStatus,
)

logger = get_logger(__name__)


class BiosManagerInterface(ABC):
    """Abstract interface for BIOS managers."""

    @abstractmethod
    def get_device_config(self, device_type: str) -> Optional[DeviceConfig]:
        """Get device configuration for the specified device type."""
        pass

    @abstractmethod
    def select_optimal_method(
        self, device_type: str, target_ip: str
    ) -> MethodSelectionResult:
        """Select the optimal BIOS configuration method for the device."""
        pass

    @abstractmethod
    def apply_bios_config_smart(
        self,
        device_type: str,
        target_ip: str,
        username: str,
        password: str,
        dry_run: bool = False,
        backup_enabled: bool = True,
    ) -> BiosConfigResult:
        """Apply BIOS configuration using smart method selection."""
        pass


class BaseBiosManagerImpl(BaseBiosManager, BiosManagerInterface):
    """Base implementation of BIOS manager with common functionality."""

    def __init__(self, config_dir: str = "configs/bios"):
        """Initialize base BIOS manager.

        Args:
            config_dir: Directory containing BIOS configuration files
        """
        super().__init__()
        self.config_dir = config_dir
        self.device_mappings = {}
        self.template_rules = {}
        self.preserve_settings = {}

    def _create_backup(
        self, config: ET.Element, device_type: str, target_ip: str
    ) -> str:
        """Create backup of current configuration.

        Args:
            config: Current configuration XML
            device_type: Device type for naming
            target_ip: Target IP for naming

        Returns:
            Path to backup file
        """
        import datetime

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"bios_backup_{device_type}_{target_ip}_{timestamp}.xml"

        # Use temp directory for backups
        backup_dir = os.path.join(tempfile.gettempdir(), "bios_backups")
        os.makedirs(backup_dir, exist_ok=True)
        backup_path = os.path.join(backup_dir, backup_filename)

        # Save backup
        ET.indent(config)
        tree = ET.ElementTree(config)
        tree.write(backup_path, encoding="utf-8", xml_declaration=True)

        return backup_path

    def list_available_device_types(self) -> List[str]:
        """Get list of all available device types.

        Returns:
            List of device type strings
        """
        return list(self.device_mappings.keys())

    def get_device_types(self) -> List[str]:
        """Get list of available device types."""
        return self.list_available_device_types()

    def get_device_type_info(self, device_type: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a device type.

        Args:
            device_type: Device type to query

        Returns:
            Dictionary with device information or None if not found
        """
        device_config = self.get_device_config(device_type)
        if not device_config:
            return None

        return {
            "device_type": device_config.device_type,
            "manufacturer": device_config.manufacturer,
            "model": device_config.model,
            "motherboard": device_config.motherboard,
            "redfish_enabled": device_config.redfish_enabled,
            "vendor_tools_available": device_config.vendor_tools_available,
            "special_handling": device_config.special_handling,
        }

    def _extract_vendor_from_mapping(self, mapping: Dict[str, Any]) -> str:
        """Extract and normalize vendor name from device mapping."""
        vendor = "Unknown"
        if "hardware_specs" in mapping and "vendor" in mapping["hardware_specs"]:
            vendor = mapping["hardware_specs"]["vendor"].title()
        elif "manufacturer" in mapping:
            vendor = mapping["manufacturer"]

        # Map vendor names to standard format
        vendor_mapping = {"hpe": "HPE", "dell": "Dell", "supermicro": "Supermicro"}
        return vendor_mapping.get(vendor.lower(), vendor)

    def _extract_model_from_mapping(self, mapping: Dict[str, Any]) -> str:
        """Extract model information from device mapping."""
        model = "Unknown"
        if "hardware_specs" in mapping and "cpu_name" in mapping["hardware_specs"]:
            model = mapping["hardware_specs"]["cpu_name"]
        elif "model" in mapping:
            model = mapping["model"]
        return model

    def _create_motherboard_list(
        self, mapping: Dict[str, Any], vendor: str, model: str
    ) -> List[str]:
        """Create motherboard list from mapping data."""
        if "motherboard" in mapping:
            return mapping["motherboard"]
        else:
            # Create from vendor and model info
            return [vendor, model]


class BiosManagerMixin:
    """Mixin providing common BIOS manager utilities."""

    @staticmethod
    def _validate_credentials(username: str, password: str) -> bool:
        """Validate authentication credentials."""
        return bool(username and password)

    @staticmethod
    def _validate_ip_address(ip_address: str) -> bool:
        """Validate IP address format."""
        import ipaddress

        try:
            ipaddress.ip_address(ip_address)
            return True
        except ValueError:
            return False

    @staticmethod
    def _create_config_result(
        success: bool,
        method: ConfigMethod,
        settings_applied: Dict[str, Any] = None,
        settings_failed: Dict[str, Any] = None,
        backup_file: Optional[str] = None,
        validation_errors: List[str] = None,
        reboot_required: bool = False,
    ) -> BiosConfigResult:
        """Create a BiosConfigResult with consistent defaults."""
        return BiosConfigResult(
            success=success,
            method_used=method,
            settings_applied=settings_applied or {},
            settings_failed=settings_failed or {},
            backup_file=backup_file,
            validation_errors=validation_errors or [],
            reboot_required=reboot_required,
        )
