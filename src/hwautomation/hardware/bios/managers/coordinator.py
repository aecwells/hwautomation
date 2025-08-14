"""
BIOS manager coordination and factory.

This module provides coordination between different BIOS managers
and factory functions for creating appropriate managers based on
device type, vendor, and capabilities.
"""

from typing import Any, Dict, List, Optional, Type

from ....logging import get_logger
from ..base import BiosConfigResult, ConfigMethod, DeviceConfig, MethodSelectionResult
from ..config.loader import ConfigurationLoader
from ..config.validator import ConfigurationValidator
from .base import BiosManagerInterface
from .ipmi import IpmiBiosManager
from .redfish import RedfishBiosManager
from .vendor import DellBiosManager, HpeBiosManager, SupermicroBiosManager

logger = get_logger(__name__)


class BiosManagerFactory:
    """Factory for creating appropriate BIOS managers based on context."""

    _manager_registry = {
        "redfish": RedfishBiosManager,
        "dell": DellBiosManager,
        "hpe": HpeBiosManager,
        "supermicro": SupermicroBiosManager,
        "ipmi": IpmiBiosManager,
    }

    @classmethod
    def create_manager(
        cls,
        manager_type: str,
        config_dir: str = "configs/bios",
    ) -> Optional[BiosManagerInterface]:
        """Create appropriate BIOS manager.

        Args:
            manager_type: Type of manager ('redfish', 'dell', 'hpe', 'supermicro', 'ipmi')
            config_dir: Configuration directory path

        Returns:
            BIOS manager instance or None if type not found
        """
        manager_class = cls._manager_registry.get(manager_type.lower())
        if not manager_class:
            logger.error(f"Unknown manager type: {manager_type}")
            return None

        try:
            return manager_class(config_dir)
        except Exception as e:
            logger.error(f"Failed to create {manager_type} manager: {e}")
            return None

    @classmethod
    def create_for_device(
        cls,
        device_type: str,
        config_dir: str = "configs/bios",
    ) -> Optional[BiosManagerInterface]:
        """Create appropriate BIOS manager for a specific device.

        Args:
            device_type: Device type identifier
            config_dir: Configuration directory path

        Returns:
            BIOS manager instance optimized for the device
        """
        # Load device mappings to determine vendor
        try:
            config_loader = ConfigurationLoader(config_dir)
            device_mappings = config_loader.load_device_mappings()

            if device_type not in device_mappings:
                logger.warning(
                    f"Device type {device_type} not found, using generic manager"
                )
                return cls.create_manager("redfish", config_dir)

            mapping = device_mappings[device_type]
            vendor = cls._extract_vendor(mapping)

            # Select manager based on vendor
            if vendor.lower() == "dell":
                return cls.create_manager("dell", config_dir)
            elif vendor.lower() == "hpe":
                return cls.create_manager("hpe", config_dir)
            elif vendor.lower() == "supermicro":
                return cls.create_manager("supermicro", config_dir)
            else:
                # Default to Redfish for unknown vendors
                return cls.create_manager("redfish", config_dir)

        except Exception as e:
            logger.error(f"Failed to create manager for device {device_type}: {e}")
            return cls.create_manager("redfish", config_dir)

    @classmethod
    def register_manager(cls, name: str, manager_class: Type[BiosManagerInterface]):
        """Register a custom BIOS manager.

        Args:
            name: Manager name
            manager_class: Manager class implementing BiosManagerInterface
        """
        cls._manager_registry[name.lower()] = manager_class
        logger.info(f"Registered custom BIOS manager: {name}")

    @classmethod
    def list_managers(cls) -> List[str]:
        """List all registered manager types."""
        return list(cls._manager_registry.keys())

    @staticmethod
    def _extract_vendor(mapping: Dict[str, Any]) -> str:
        """Extract vendor from device mapping."""
        if "hardware_specs" in mapping and "vendor" in mapping["hardware_specs"]:
            return mapping["hardware_specs"]["vendor"].title()
        elif "manufacturer" in mapping:
            return mapping["manufacturer"]
        return "Unknown"


class BiosManagerCoordinator:
    """Coordinates BIOS operations across multiple managers."""

    def __init__(self, config_dir: str = "configs/bios"):
        """Initialize BIOS manager coordinator.

        Args:
            config_dir: Configuration directory path
        """
        self.config_dir = config_dir
        self.factory = BiosManagerFactory()
        self._manager_cache = {}

    def get_manager(self, manager_type: str) -> Optional[BiosManagerInterface]:
        """Get or create a BIOS manager.

        Args:
            manager_type: Type of manager to get

        Returns:
            BIOS manager instance
        """
        if manager_type not in self._manager_cache:
            self._manager_cache[manager_type] = self.factory.create_manager(
                manager_type, self.config_dir
            )
        return self._manager_cache[manager_type]

    def get_manager_for_device(
        self, device_type: str
    ) -> Optional[BiosManagerInterface]:
        """Get appropriate BIOS manager for a device.

        Args:
            device_type: Device type identifier

        Returns:
            BIOS manager instance optimized for the device
        """
        cache_key = f"device_{device_type}"
        if cache_key not in self._manager_cache:
            self._manager_cache[cache_key] = self.factory.create_for_device(
                device_type, self.config_dir
            )
        return self._manager_cache[cache_key]

    def apply_bios_config(
        self,
        device_type: str,
        target_ip: str,
        username: str,
        password: str,
        manager_type: Optional[str] = None,
        dry_run: bool = False,
        backup_enabled: bool = True,
    ) -> BiosConfigResult:
        """Apply BIOS configuration with automatic manager selection.

        Args:
            device_type: Target device type
            target_ip: Target system IP address
            username: Authentication username
            password: Authentication password
            manager_type: Specific manager type to use (optional)
            dry_run: If True, validate but don't apply changes
            backup_enabled: If True, create backup before changes

        Returns:
            BiosConfigResult with operation details
        """
        # Select appropriate manager
        if manager_type:
            manager = self.get_manager(manager_type)
        else:
            manager = self.get_manager_for_device(device_type)

        if not manager:
            return BiosConfigResult(
                success=False,
                method_used=ConfigMethod.MANUAL,
                settings_applied={},
                settings_failed={"error": "No suitable BIOS manager available"},
                validation_errors=["Failed to create BIOS manager"],
            )

        # Apply configuration using selected manager
        return manager.apply_bios_config_smart(
            device_type=device_type,
            target_ip=target_ip,
            username=username,
            password=password,
            dry_run=dry_run,
            backup_enabled=backup_enabled,
        )

    def select_optimal_method(
        self, device_type: str, target_ip: str
    ) -> MethodSelectionResult:
        """Select optimal BIOS configuration method.

        Args:
            device_type: Target device type
            target_ip: Target system IP address

        Returns:
            MethodSelectionResult with analysis from best manager
        """
        manager = self.get_manager_for_device(device_type)
        if not manager:
            return MethodSelectionResult(
                recommended_method=ConfigMethod.MANUAL,
                available_methods=[ConfigMethod.MANUAL],
                redfish_capabilities={},
                vendor_tools_status={},
                confidence_score=0.0,
                reasoning="No suitable BIOS manager available",
                fallback_methods=[],
            )

        return manager.select_optimal_method(device_type, target_ip)

    def get_device_config(self, device_type: str) -> Optional[DeviceConfig]:
        """Get device configuration using appropriate manager.

        Args:
            device_type: Target device type

        Returns:
            DeviceConfig object or None if not found
        """
        manager = self.get_manager_for_device(device_type)
        if not manager:
            return None

        return manager.get_device_config(device_type)

    def list_available_device_types(self) -> List[str]:
        """Get list of all available device types.

        Returns:
            List of device type strings
        """
        try:
            config_loader = ConfigurationLoader(self.config_dir)
            device_mappings = config_loader.load_device_mappings()
            return list(device_mappings.keys())
        except Exception as e:
            logger.error(f"Failed to load device types: {e}")
            return []

    def get_device_type_info(self, device_type: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a device type.

        Args:
            device_type: Device type to query

        Returns:
            Dictionary with device information or None if not found
        """
        manager = self.get_manager_for_device(device_type)
        if not manager:
            return None

        return manager.get_device_type_info(device_type)


# Global coordinator instance
coordinator = BiosManagerCoordinator()


# Convenience functions
def apply_bios_config(
    device_type: str,
    target_ip: str,
    username: str,
    password: str,
    manager_type: Optional[str] = None,
    dry_run: bool = False,
    backup_enabled: bool = True,
) -> BiosConfigResult:
    """Convenience function for BIOS configuration."""
    return coordinator.apply_bios_config(
        device_type=device_type,
        target_ip=target_ip,
        username=username,
        password=password,
        manager_type=manager_type,
        dry_run=dry_run,
        backup_enabled=backup_enabled,
    )


def select_optimal_method(device_type: str, target_ip: str) -> MethodSelectionResult:
    """Convenience function for method selection."""
    return coordinator.select_optimal_method(device_type, target_ip)


def get_device_config(device_type: str) -> Optional[DeviceConfig]:
    """Convenience function for device configuration."""
    return coordinator.get_device_config(device_type)
