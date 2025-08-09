"""Dell device handler for BIOS configuration.

This module provides Dell-specific BIOS configuration handling including
Redfish integration and vendor-specific settings.
"""

import xml.etree.ElementTree as ET
from typing import List, Optional

from ....logging import get_logger
from ..base import BaseDeviceHandler, ConfigMethod, DeviceConfig

logger = get_logger(__name__)


class DellDeviceHandler(BaseDeviceHandler):
    """Dell-specific BIOS configuration handler."""

    def __init__(self, device_config: DeviceConfig):
        """Initialize Dell device handler.

        Args:
            device_config: Dell device configuration
        """
        super().__init__(device_config)
        self.dell_specific_settings = {
            "BootMode": "Uefi",
            "SecureBoot": "Enabled",
            "ProcVirtualization": "Enabled",
            "VtForDirectIo": "Enabled",
            "SriovGlobalEnable": "Enabled",
        }

    def can_handle(self, device_type: str) -> bool:
        """Check if this handler can manage the given device type.

        Args:
            device_type: Device type to check

        Returns:
            True if this handler can manage the device type
        """
        # Dell devices typically use 'a1' prefix in our naming scheme
        return (
            device_type.startswith("a1.")
            or self.device_config.manufacturer.lower() == "dell"
        )

    def get_supported_methods(self) -> List[ConfigMethod]:
        """Get list of supported configuration methods for Dell devices.

        Returns:
            List of supported configuration methods
        """
        methods = []

        # Dell has good Redfish support
        if self.device_config.redfish_enabled:
            methods.append(ConfigMethod.REDFISH_STANDARD)
            methods.append(ConfigMethod.REDFISH_OEM)

        # Dell has vendor tools (RACADM, etc.)
        if self.device_config.vendor_tools_available:
            methods.append(ConfigMethod.VENDOR_TOOLS)

        # Hybrid approach combining Redfish and vendor tools
        if methods:
            methods.append(ConfigMethod.HYBRID)

        # Manual configuration always available as fallback
        methods.append(ConfigMethod.MANUAL)

        return methods

    def apply_device_specific_settings(self, config: ET.Element) -> ET.Element:
        """Apply Dell-specific BIOS settings.

        Args:
            config: Current configuration XML

        Returns:
            Modified configuration XML with Dell-specific settings
        """
        self.logger.info("Applying Dell-specific BIOS settings")

        try:
            # Apply Dell-specific settings
            for setting_name, setting_value in self.dell_specific_settings.items():
                self._set_bios_attribute(config, setting_name, setting_value)

            # Apply device-type specific settings
            self._apply_device_type_settings(config)

            # Apply special handling if configured
            if self.device_config.special_handling:
                self._apply_special_handling(config)

            self.logger.info("Successfully applied Dell-specific settings")
            return config

        except Exception as e:
            self.logger.error(f"Failed to apply Dell-specific settings: {e}")
            raise

    def _set_bios_attribute(self, config: ET.Element, name: str, value: str) -> None:
        """Set a BIOS attribute in the configuration.

        Args:
            config: Configuration XML
            name: Attribute name
            value: Attribute value
        """
        # Find the attribute in the configuration
        attribute = self._find_attribute(config, name)

        if attribute is not None:
            # Update existing attribute
            attribute.text = value
            self.logger.debug(f"Updated Dell attribute {name} = {value}")
        else:
            # Create new attribute if it doesn't exist
            self._create_attribute(config, name, value)
            self.logger.debug(f"Created Dell attribute {name} = {value}")

    def _find_attribute(self, config: ET.Element, name: str) -> Optional[ET.Element]:
        """Find an attribute by name in the configuration.

        Args:
            config: Configuration XML
            name: Attribute name to find

        Returns:
            Attribute element or None if not found
        """
        for attribute in config.findall(".//Attribute"):
            if attribute.get("Name") == name:
                return attribute
        return None

    def _create_attribute(self, config: ET.Element, name: str, value: str) -> None:
        """Create a new attribute in the configuration.

        Args:
            config: Configuration XML
            name: Attribute name
            value: Attribute value
        """
        # Find or create BIOS component
        bios_component = None
        for component in config.findall(".//Component"):
            if component.get("FQDD") == "BIOS.Setup.1-1":
                bios_component = component
                break

        if bios_component is None:
            # Create BIOS component if it doesn't exist
            bios_component = ET.SubElement(config, "Component")
            bios_component.set("FQDD", "BIOS.Setup.1-1")

        # Create new attribute
        attribute = ET.SubElement(bios_component, "Attribute")
        attribute.set("Name", name)
        attribute.text = value

    def _apply_device_type_settings(self, config: ET.Element) -> None:
        """Apply device-type specific settings for Dell devices.

        Args:
            config: Configuration XML
        """
        device_type = self.device_config.device_type

        # Apply settings based on device type patterns
        if ".c5." in device_type:
            # High-performance compute settings
            self._set_bios_attribute(config, "CpuInterconnectBusSpeed", "MaxDataRate")
            self._set_bios_attribute(config, "MemOpMode", "OptimizerMode")

        elif ".c2." in device_type:
            # Balanced performance settings
            self._set_bios_attribute(config, "CpuInterconnectBusSpeed", "Auto")
            self._set_bios_attribute(config, "MemOpMode", "AdvEccMode")

        elif ".c1." in device_type:
            # Basic configuration settings
            self._set_bios_attribute(config, "CpuInterconnectBusSpeed", "Auto")
            self._set_bios_attribute(config, "MemOpMode", "AdvEccMode")

    def _apply_special_handling(self, config: ET.Element) -> None:
        """Apply special handling configuration.

        Args:
            config: Configuration XML
        """
        special_handling = self.device_config.special_handling

        if "custom_settings" in special_handling:
            custom_settings = special_handling["custom_settings"]
            for setting_name, setting_value in custom_settings.items():
                self._set_bios_attribute(config, setting_name, setting_value)
                self.logger.debug(
                    f"Applied custom Dell setting {setting_name} = {setting_value}"
                )

    def get_priority(self) -> int:
        """Get priority for Dell device handler selection.

        Returns:
            Priority value (lower = higher priority)
        """
        return 10  # High priority for Dell devices

    def get_redfish_settings_map(self) -> dict:
        """Get mapping of BIOS settings to Redfish attribute names.

        Returns:
            Dictionary mapping BIOS setting names to Redfish paths
        """
        return {
            "BootMode": "/redfish/v1/Systems/System.Embedded.1/Bios/Attributes/BootMode",
            "SecureBoot": "/redfish/v1/Systems/System.Embedded.1/SecureBoot",
            "ProcVirtualization": "/redfish/v1/Systems/System.Embedded.1/Bios/Attributes/ProcVirtualization",
            "VtForDirectIo": "/redfish/v1/Systems/System.Embedded.1/Bios/Attributes/VtForDirectIo",
            "SriovGlobalEnable": "/redfish/v1/Systems/System.Embedded.1/Bios/Attributes/SriovGlobalEnable",
        }

    def validate_dell_specific_settings(self, config: ET.Element) -> List[str]:
        """Validate Dell-specific BIOS settings.

        Args:
            config: Configuration to validate

        Returns:
            List of validation errors
        """
        errors = []

        # Check required Dell settings
        required_settings = ["BootMode", "SecureBoot"]
        for setting in required_settings:
            attribute = self._find_attribute(config, setting)
            if attribute is None:
                errors.append(f"Missing required Dell setting: {setting}")
            elif not attribute.text:
                errors.append(f"Empty value for Dell setting: {setting}")

        # Validate setting values
        boot_mode = self._find_attribute(config, "BootMode")
        if boot_mode is not None and boot_mode.text not in ["Bios", "Uefi"]:
            errors.append(f"Invalid BootMode value: {boot_mode.text}")

        secure_boot = self._find_attribute(config, "SecureBoot")
        if secure_boot is not None and secure_boot.text not in ["Enabled", "Disabled"]:
            errors.append(f"Invalid SecureBoot value: {secure_boot.text}")

        return errors
