"""Main BIOS configuration manager - coordinates all BIOS operations.

DEPRECATED: This module has been refactored into a modular system.
Please import from hwautomation.hardware.bios.managers instead.

This module provides backward compatibility for existing imports while the
codebase migrates to the new modular BIOS manager system.

Migration examples:
    # Old import
    from hwautomation.hardware.bios.manager import BiosConfigManager

    # New import
    from hwautomation.hardware.bios.managers import coordinator

The new modular system provides:
- Vendor-specific BIOS managers
- Protocol-specific implementations (Redfish, IPMI)
- Factory pattern for automatic manager selection
- Enhanced error handling and validation
"""

import warnings
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Union

# Issue deprecation warning
warnings.warn(
    "hwautomation.hardware.bios.manager is deprecated. "
    "Please import from hwautomation.hardware.bios.managers instead. "
    "This module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

from .base import BiosConfigResult, ConfigMethod, DeviceConfig, MethodSelectionResult

# Import from new modular location for backward compatibility
from .managers import (
    BiosManagerCoordinator,
    RedfishBiosManager,
    apply_bios_config,
    coordinator,
    get_device_config,
    select_optimal_method,
)


class BiosConfigManager:
    """
    Backward compatibility wrapper for the original BiosConfigManager.

    This class delegates to the new modular system while maintaining
    the original interface.
    """

    def __init__(self, config_dir: str = "configs/bios"):
        """Initialize BIOS configuration manager.

        Args:
            config_dir: Directory containing BIOS configuration files
        """
        self.config_dir = config_dir
        self._coordinator = BiosManagerCoordinator(config_dir)

        # Initialize legacy attributes for compatibility
        self.device_mappings = {}
        self.template_rules = {}
        self.preserve_settings = {}

        # Load configurations for compatibility
        self._load_configurations()

    def _load_configurations(self) -> None:
        """Load all configuration files for compatibility."""
        try:
            from .config.loader import ConfigurationLoader

            config_loader = ConfigurationLoader(self.config_dir)
            self.device_mappings = config_loader.load_device_mappings()
            self.template_rules = config_loader.load_template_rules()
            self.preserve_settings = config_loader.load_preserve_settings()
        except Exception:
            # Initialize with empty configs to prevent crashes
            self.device_mappings = {}
            self.template_rules = {}
            self.preserve_settings = {}

    def get_device_config(self, device_type: str) -> Optional[DeviceConfig]:
        """Get device configuration for the specified device type."""
        return self._coordinator.get_device_config(device_type)

    def select_optimal_method(
        self, device_type: str, target_ip: str
    ) -> MethodSelectionResult:
        """Select the optimal BIOS configuration method for the device."""
        return self._coordinator.select_optimal_method(device_type, target_ip)

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
        return self._coordinator.apply_bios_config(
            device_type=device_type,
            target_ip=target_ip,
            username=username,
            password=password,
            dry_run=dry_run,
            backup_enabled=backup_enabled,
        )

    def list_available_device_types(self) -> List[str]:
        """Get list of all available device types."""
        return self._coordinator.list_available_device_types()

    def get_device_type_info(self, device_type: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a device type."""
        return self._coordinator.get_device_type_info(device_type)

    def get_device_types(self) -> List[str]:
        """Get list of available device types."""
        return self.list_available_device_types()

    # Legacy methods that delegate to Redfish manager for compatibility
    def pull_current_config(
        self, target_ip: str, username: str, password: str
    ) -> ET.Element:
        """Pull current BIOS configuration from target system."""
        manager = self._coordinator.get_manager("redfish")
        if hasattr(manager, "_get_redfish_bios_config"):
            return manager._get_redfish_bios_config(target_ip, username, password)
        return ET.Element("BiosConfiguration")

    def apply_template(self, config: ET.Element, device_type: str) -> ET.Element:
        """Apply template modifications to configuration."""
        manager = self._coordinator.get_manager_for_device(device_type)
        if hasattr(manager, "_apply_redfish_template"):
            return manager._apply_redfish_template(config, device_type)
        return config

    def validate_config(self, config: ET.Element, device_type: str) -> List[str]:
        """Validate modified configuration."""
        manager = self._coordinator.get_manager_for_device(device_type)
        if hasattr(manager, "_validate_redfish_config"):
            return manager._validate_redfish_config(config, device_type)
        return []

    def push_config(
        self, config: ET.Element, target_ip: str, username: str, password: str
    ) -> bool:
        """Push modified configuration to target system."""
        manager = self._coordinator.get_manager("redfish")
        if hasattr(manager, "_apply_redfish_bios_config"):
            return manager._apply_redfish_bios_config(
                config, target_ip, username, password
            )
        return False

    def test_redfish_connection(
        self, target_ip: str, username: str, password: str
    ) -> tuple[bool, str]:
        """Test Redfish connection for BIOS management."""
        manager = self._coordinator.get_manager("redfish")
        if hasattr(manager, "test_redfish_connection"):
            return manager.test_redfish_connection(target_ip, username, password)
        return False, "Redfish manager not available"

    def get_system_info_via_redfish(self, target_ip: str, username: str, password: str):
        """Get system information via Redfish."""
        manager = self._coordinator.get_manager("redfish")
        if hasattr(manager, "get_system_info_via_redfish"):
            return manager.get_system_info_via_redfish(target_ip, username, password)
        return None

    def determine_bios_config_method(
        self, target_ip: str, device_type: str, username: str, password: str
    ) -> str:
        """Determine the best BIOS configuration method."""
        result = self.select_optimal_method(device_type, target_ip)
        method_map = {
            ConfigMethod.REDFISH_STANDARD: "redfish",
            ConfigMethod.VENDOR_TOOLS: "vendor_tool",
            ConfigMethod.MANUAL: "hybrid",
        }
        return method_map.get(result.recommended_method, "hybrid")

    async def apply_bios_config_phase3(
        self,
        device_type: str,
        target_ip: str,
        username: str = "ADMIN",
        password: Optional[str] = None,
        dry_run: bool = False,
        prefer_performance: bool = True,
        enable_monitoring: bool = True,
    ) -> Dict[str, Any]:
        """Real-time monitored BIOS configuration with advanced error recovery."""
        # Delegate to the regular apply_bios_config_smart method
        result = self.apply_bios_config_smart(
            device_type=device_type,
            target_ip=target_ip,
            username=username,
            password=password,
            dry_run=dry_run,
        )

        # Convert BiosConfigResult to phase3 format for compatibility
        return {
            "success": result.success,
            "target_ip": target_ip,
            "device_type": device_type,
            "operation_id": None,
            "monitoring_enabled": enable_monitoring,
            "method_analysis": {
                "method": result.method_used.value if result.method_used else "unknown"
            },
            "execution_phases": [{"phase": "configuration", "success": result.success}],
            "real_time_progress": [],
            "error_recovery_actions": [],
            "validation_results": {"success": result.success},
            "performance_metrics": {},
            "dry_run": dry_run,
            "settings_applied": result.settings_applied,
            "settings_failed": result.settings_failed,
            "validation_errors": result.validation_errors or [],
        }
