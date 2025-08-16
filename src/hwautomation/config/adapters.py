"""
Backward compatibility adapters for unified configuration.

These adapters transform the unified configuration structure into the formats
expected by existing BIOS and firmware management systems, allowing for
seamless migration without breaking changes.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

from ..logging import get_logger
from .unified_loader import UnifiedConfigLoader

logger = get_logger(__name__)


class BiosConfigAdapter:
    """
    Adapter to provide BIOS configuration in the old device_mappings.yaml format.

    This allows existing BIOS management code to continue working unchanged
    while using the unified configuration as the source of truth.
    """

    def __init__(self, unified_loader: Optional[UnifiedConfigLoader] = None):
        """
        Initialize BIOS configuration adapter.

        Args:
            unified_loader: Optional UnifiedConfigLoader instance. If None, creates new one.
        """
        self.loader = unified_loader or UnifiedConfigLoader()
        logger.debug("Initialized BiosConfigAdapter")

    def load_device_mappings(self) -> Dict[str, Any]:
        """
        Load device mappings in the legacy format.

        This method transforms the unified configuration into the format
        expected by the existing BIOS configuration system.

        Returns:
            Dictionary in device_mappings.yaml format
        """
        try:
            device_types = {}
            all_device_types = self.loader.list_all_device_types()

            for device_type in all_device_types:
                device_info = self.loader.get_device_by_type(device_type)
                if not device_info:
                    continue

                # Transform to legacy format
                device_config = device_info.device_config
                device_types[device_type] = {
                    "description": device_config.get("description", ""),
                    "hardware_specs": device_config.get("hardware_specs", {}),
                    "boot_configs": device_config.get("boot_configs", {}),
                    "cpu_configs": device_config.get("cpu_configs", {}),
                    "memory_configs": device_config.get("memory_configs", {}),
                    "security_configs": device_config.get("security_configs", {}),
                    "bios_settings": device_config.get("bios_settings", {}),
                    "bios_setting_methods": device_config.get(
                        "bios_setting_methods", {}
                    ),
                    "redfish_capable": device_config.get("redfish_capable", True),
                    "preferred_bios_method": device_config.get(
                        "preferred_bios_method", "hybrid"
                    ),
                    "fallback_bios_method": device_config.get(
                        "fallback_bios_method", "vendor_tool"
                    ),
                    # Legacy fields
                    "motherboards": [device_info.motherboard],
                    "vendor": device_info.vendor,
                    # Redfish settings if available
                    "redfish_settings": device_config.get("redfish_settings", []),
                    "vendor_only_settings": device_config.get(
                        "vendor_only_settings", []
                    ),
                    "method_performance": device_config.get("method_performance", {}),
                    "redfish_compatibility": device_config.get(
                        "redfish_compatibility", {}
                    ),
                }

            logger.info(f"Converted {len(device_types)} device types to legacy format")
            return device_types

        except Exception as e:
            logger.error(f"Failed to load device mappings: {e}")
            return {}

    def load_template_rules(self) -> Dict[str, Any]:
        """
        Load template rules (placeholder for now).

        TODO: Implement template rules loading from unified config
        or maintain separate file for now.

        Returns:
            Dictionary containing template rules
        """
        # For now, return empty dict as template rules are not yet migrated
        # This can be extended later to include template rules in unified config
        return {}

    def load_preserve_settings(self) -> Dict[str, Any]:
        """
        Load preserve settings (placeholder for now).

        TODO: Implement preserve settings loading from unified config
        or maintain separate file for now.

        Returns:
            Dictionary containing preserve settings
        """
        # For now, return empty dict as preserve settings are not yet migrated
        return {}

    def get_device_motherboards(self, device_type: str) -> List[str]:
        """
        Get motherboards for a device type.

        Args:
            device_type: Device type identifier

        Returns:
            List of motherboard names
        """
        device_info = self.loader.get_device_by_type(device_type)
        return [device_info.motherboard] if device_info else []

    def get_device_vendor(self, device_type: str) -> Optional[str]:
        """
        Get vendor for a device type.

        Args:
            device_type: Device type identifier

        Returns:
            Vendor name or None if not found
        """
        device_info = self.loader.get_device_by_type(device_type)
        return device_info.vendor if device_info else None

    def validate_device_config(self, device_type: str) -> Dict[str, Any]:
        """
        Validate device configuration.

        Args:
            device_type: Device type to validate

        Returns:
            Dictionary with validation results
        """
        device_info = self.loader.get_device_by_type(device_type)

        if not device_info:
            return {
                "valid": False,
                "errors": [f"Device type {device_type} not found"],
                "warnings": [],
            }

        errors = []
        warnings = []

        # Basic validation
        device_config = device_info.device_config

        if not device_config.get("description"):
            warnings.append("Missing device description")

        if not device_config.get("hardware_specs"):
            errors.append("Missing hardware specifications")

        if not device_config.get("boot_configs"):
            warnings.append("Missing boot configurations")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


class FirmwareConfigAdapter:
    """
    Adapter to provide firmware configuration in the old firmware_repository.yaml format.

    This allows existing firmware management code to continue working unchanged
    while using the unified configuration as the source of truth.
    """

    def __init__(self, unified_loader: Optional[UnifiedConfigLoader] = None):
        """
        Initialize firmware configuration adapter.

        Args:
            unified_loader: Optional UnifiedConfigLoader instance. If None, creates new one.
        """
        self.loader = unified_loader or UnifiedConfigLoader()
        logger.debug("Initialized FirmwareConfigAdapter")

    def load_firmware_repository(self) -> Dict[str, Any]:
        """
        Load firmware repository in the legacy format.

        This method transforms the unified configuration into the format
        expected by the existing firmware management system.

        Returns:
            Dictionary in firmware_repository.yaml format
        """
        try:
            global_settings = self.loader.get_global_settings()

            # Build legacy firmware repository structure
            firmware_repo = {
                "firmware_repository": {
                    "global_settings": global_settings.get("firmware", {}),
                    "vendors": {},
                }
            }

            # Process each vendor
            for vendor_name in self.loader.list_vendors():
                vendor_info = self.loader.get_vendor_info(vendor_name)
                if not vendor_info:
                    continue

                vendor_data = vendor_info["vendor_info"]

                # Build vendor structure
                firmware_vendor = {
                    "display_name": vendor_data.get(
                        "display_name", vendor_name.title()
                    ),
                    "support_url": vendor_data.get("support_url", ""),
                    "bios": vendor_data.get("firmware", {}).get("bios", {}),
                    "bmc": vendor_data.get("firmware", {}).get("bmc", {}),
                    "tools": vendor_data.get("firmware", {}).get("tools", {}),
                    "motherboards": {},
                }

                # Add motherboards for this vendor
                motherboards = self.loader.list_motherboards(vendor_name)
                for motherboard_name in motherboards:
                    motherboard_info = self.loader.get_motherboard_info(
                        motherboard_name
                    )
                    if motherboard_info:
                        motherboard_data = motherboard_info["motherboard_info"]
                        firmware_vendor["motherboards"][motherboard_name] = {
                            "model": motherboard_name,
                            "firmware_tracking": motherboard_data.get(
                                "firmware_tracking",
                                {
                                    "bios": {
                                        "current_version": "unknown",
                                        "latest_version": "unknown",
                                        "update_available": False,
                                        "files": [],
                                    },
                                    "bmc": {
                                        "current_version": "unknown",
                                        "latest_version": "unknown",
                                        "update_available": False,
                                        "files": [],
                                    },
                                },
                            ),
                        }

                firmware_repo["firmware_repository"]["vendors"][
                    vendor_name
                ] = firmware_vendor

            logger.info(
                f"Converted {len(firmware_repo['firmware_repository']['vendors'])} vendors to legacy format"
            )
            return firmware_repo

        except Exception as e:
            logger.error(f"Failed to load firmware repository: {e}")
            return {"firmware_repository": {"global_settings": {}, "vendors": {}}}

    def get_vendor_tools(self, vendor: str) -> Dict[str, Any]:
        """
        Get vendor-specific tools configuration.

        Args:
            vendor: Vendor name

        Returns:
            Dictionary containing vendor tools
        """
        vendor_info = self.loader.get_vendor_info(vendor)
        if vendor_info:
            return vendor_info["vendor_info"].get("firmware", {}).get("tools", {})
        return {}

    def get_motherboard_firmware_info(
        self, motherboard: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get firmware information for a specific motherboard.

        Args:
            motherboard: Motherboard model name

        Returns:
            Dictionary with firmware information or None if not found
        """
        motherboard_info = self.loader.get_motherboard_info(motherboard)
        if motherboard_info:
            return motherboard_info["motherboard_info"].get("firmware_tracking")
        return None

    def get_firmware_files(
        self, motherboard: str, component: str = "bios"
    ) -> List[str]:
        """
        Get firmware files for a motherboard component.

        Args:
            motherboard: Motherboard model name
            component: Component type ('bios' or 'bmc')

        Returns:
            List of firmware file paths
        """
        firmware_info = self.get_motherboard_firmware_info(motherboard)
        if firmware_info and component in firmware_info:
            return firmware_info[component].get("files", [])
        return []

    def update_firmware_tracking(
        self, motherboard: str, component: str, version_info: Dict[str, Any]
    ) -> bool:
        """
        Update firmware tracking information.

        Note: This is a placeholder for now. In a full implementation,
        this would update the unified configuration file.

        Args:
            motherboard: Motherboard model name
            component: Component type ('bios' or 'bmc')
            version_info: Version information to update

        Returns:
            True if successful, False otherwise
        """
        # TODO: Implement updating the unified configuration file
        # For now, just log the operation
        logger.info(
            f"Would update {component} firmware tracking for {motherboard}: {version_info}"
        )
        return True

    def get_firmware_config(self) -> Dict[str, Any]:
        """
        Get firmware configuration in the expected format.

        Returns:
            Dictionary containing firmware configuration
        """
        return self.load_firmware_repository()


class ConfigurationManager:
    """
    Main configuration manager that provides unified access to all configurations.

    This class coordinates between the unified loader and backward compatibility
    adapters to provide a single interface for all configuration needs.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to unified configuration file
        """
        self.unified_loader = UnifiedConfigLoader(config_path)
        self.bios_adapter = BiosConfigAdapter(self.unified_loader)
        self.firmware_adapter = FirmwareConfigAdapter(self.unified_loader)

        logger.info("Initialized ConfigurationManager with unified configuration")

    def get_unified_loader(self) -> UnifiedConfigLoader:
        """Get the unified configuration loader."""
        return self.unified_loader

    def get_bios_adapter(self) -> BiosConfigAdapter:
        """Get the BIOS configuration adapter."""
        return self.bios_adapter

    def get_firmware_adapter(self) -> FirmwareConfigAdapter:
        """Get the firmware configuration adapter."""
        return self.firmware_adapter

    def reload_all_configs(self) -> None:
        """Reload all configurations from disk."""
        self.unified_loader.reload_config()
        logger.info("Reloaded all configurations")

    def get_system_status(self) -> Dict[str, Any]:
        """
        Get overall system configuration status.

        Returns:
            Dictionary with system status information
        """
        stats = self.unified_loader.get_stats()

        return {
            "config_version": self.unified_loader.get_version(),
            "last_updated": self.unified_loader.get_last_updated(),
            "statistics": {
                "vendors": stats.vendors,
                "motherboards": stats.motherboards,
                "device_types": stats.device_types,
                "firmware_files": stats.total_firmware_files,
            },
            "adapters": {"bios_compatible": True, "firmware_compatible": True},
        }

    def get_status(self) -> Dict[str, Any]:
        """Get adapter status for backward compatibility."""
        return {"bios_compatible": True, "firmware_compatible": True}

    def get_firmware_config(self) -> Optional[Dict[str, Any]]:
        """Get firmware configuration from unified config."""
        try:
            return self.firmware_adapter.get_firmware_config()
        except Exception as e:
            logger.error(f"Error getting firmware config: {e}")
            return None
