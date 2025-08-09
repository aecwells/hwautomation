"""Supermicro device handler for BIOS configuration.

This module provides Supermicro-specific BIOS configuration handling including
vendor-specific settings and tools integration.
"""

import xml.etree.ElementTree as ET
from typing import List, Optional

from ....logging import get_logger
from ..base import BaseDeviceHandler, ConfigMethod, DeviceConfig

logger = get_logger(__name__)


class SupermicroDeviceHandler(BaseDeviceHandler):
    """Supermicro-specific BIOS configuration handler."""

    def __init__(self, device_config: DeviceConfig):
        """Initialize Supermicro device handler.

        Args
        ----
            device_config: Supermicro device configuration
        """
        super().__init__(device_config)
        self.supermicro_specific_settings = {
            "Boot_mode": "UEFI",
            "Secure_Boot": "Enabled",
            "Hyper_Threading": "Enabled",
            "VT_x": "Enabled",
            "VT_d": "Enabled",
        }

    def can_handle(self, device_type: str) -> bool:
        """Check if this handler can manage the given device type.

        Args
        ----
            device_type: Device type to check

        Returns
        -------
            True if this handler can manage the device type
        """
        # Supermicro devices or explicit manufacturer match
        return (
            device_type.startswith("s2.")
            or self.device_config.manufacturer.lower() == "supermicro"
        )

    def get_supported_methods(self) -> List[ConfigMethod]:
        """Get list of supported configuration methods for Supermicro devices.

        Returns
        -------
            List of supported configuration methods
        """
        methods = []

        # Supermicro has limited Redfish support (varies by model)
        if self.device_config.redfish_enabled:
            methods.append(ConfigMethod.REDFISH_STANDARD)

        # Supermicro has vendor tools (SUM, etc.)
        if self.device_config.vendor_tools_available:
            methods.append(ConfigMethod.VENDOR_TOOLS)

        # Manual configuration always available as fallback
        methods.append(ConfigMethod.MANUAL)

        return methods

    def apply_device_specific_settings(self, config: ET.Element) -> ET.Element:
        """Apply Supermicro-specific BIOS settings.

        Args
        ----
            config: Current configuration XML

        Returns
        -------
            Modified configuration XML with Supermicro-specific settings
        """
        self.logger.info("Applying Supermicro-specific BIOS settings")

        try:
            # Apply Supermicro-specific settings
            for (
                setting_name,
                setting_value,
            ) in self.supermicro_specific_settings.items():
                self._set_bios_attribute(config, setting_name, setting_value)

            # Apply device-type specific settings
            self._apply_device_type_settings(config)

            # Apply special handling if configured
            if self.device_config.special_handling:
                self._apply_special_handling(config)

            self.logger.info("Successfully applied Supermicro-specific settings")
            return config

        except Exception as e:
            self.logger.error(f"Failed to apply Supermicro-specific settings: {e}")
            raise

    def _set_bios_attribute(self, config: ET.Element, name: str, value: str) -> None:
        """Set a BIOS attribute in the configuration.

        Args
        ----
            config: Configuration XML
            name: Attribute name
            value: Attribute value
        """
        # Find the attribute in the configuration
        attribute = self._find_attribute(config, name)

        if attribute is not None:
            # Update existing attribute
            attribute.text = value
            self.logger.debug(f"Updated Supermicro attribute {name} = {value}")
        else:
            # Create new attribute if it doesn't exist
            self._create_attribute(config, name, value)
            self.logger.debug(f"Created Supermicro attribute {name} = {value}")

    def _find_attribute(self, config: ET.Element, name: str) -> Optional[ET.Element]:
        """Find an attribute by name in the configuration.

        Args
        ----
            config: Configuration XML
            name: Attribute name to find

        Returns
        -------
            Attribute element or None if not found
        """
        for attribute in config.findall(".//Attribute"):
            if attribute.get("Name") == name:
                return attribute
        return None

    def _create_attribute(self, config: ET.Element, name: str, value: str) -> None:
        """Create a new attribute in the configuration.

        Args
        ----
            config: Configuration XML
            name: Attribute name
            value: Attribute value
        """
        # Find or create BIOS component (Supermicro uses specific naming)
        bios_component = None
        for component in config.findall(".//Component"):
            fqdd = component.get("FQDD", "")
            if "BIOS" in fqdd or fqdd.startswith("Setup"):
                bios_component = component
                break

        if bios_component is None:
            # Create BIOS component if it doesn't exist
            bios_component = ET.SubElement(config, "Component")
            bios_component.set("FQDD", "Setup.1")

        # Create new attribute
        attribute = ET.SubElement(bios_component, "Attribute")
        attribute.set("Name", name)
        attribute.text = value

    def _apply_device_type_settings(self, config: ET.Element) -> None:
        """Apply device-type specific settings for Supermicro devices.

        Args
        ----
            config: Configuration XML
        """
        device_type = self.device_config.device_type

        # Apply settings based on device type patterns
        if ".c2." in device_type:
            # Medium performance settings for Supermicro
            self._set_bios_attribute(
                config, "CPU_Power_and_Performance_Policy", "Performance"
            )
            self._set_bios_attribute(config, "Package_C_State_Limit", "C0_C1_State")

        elif ".c1." in device_type:
            # Basic configuration settings for Supermicro
            self._set_bios_attribute(
                config, "CPU_Power_and_Performance_Policy", "Balanced_Performance"
            )
            self._set_bios_attribute(config, "Package_C_State_Limit", "Auto")

    def _apply_special_handling(self, config: ET.Element) -> None:
        """Apply special handling configuration.

        Args
        ----
            config: Configuration XML
        """
        special_handling = self.device_config.special_handling

        if special_handling and "custom_settings" in special_handling:
            custom_settings = special_handling["custom_settings"]
            for setting_name, setting_value in custom_settings.items():
                self._set_bios_attribute(config, setting_name, setting_value)
                self.logger.debug(
                    f"Applied custom Supermicro setting {setting_name} = {setting_value}"
                )

    def get_priority(self) -> int:
        """Get priority for Supermicro device handler selection.

        Returns
        -------
            Priority value (lower = higher priority)
        """
        return 30  # Medium priority for Supermicro devices

    def get_redfish_settings_map(self) -> dict:
        """Get mapping of BIOS settings to Redfish attribute names for Supermicro.

        Returns
        -------
            Dictionary mapping BIOS setting names to Redfish paths
        """
        return {
            "Boot_mode": "/redfish/v1/Systems/1/Bios/Attributes/Boot_mode",
            "Secure_Boot": "/redfish/v1/Systems/1/SecureBoot",
            "Hyper_Threading": "/redfish/v1/Systems/1/Bios/Attributes/Hyper_Threading",
            "VT_x": "/redfish/v1/Systems/1/Bios/Attributes/VT_x",
            "VT_d": "/redfish/v1/Systems/1/Bios/Attributes/VT_d",
        }

    def validate_supermicro_specific_settings(self, config: ET.Element) -> List[str]:
        """Validate Supermicro-specific BIOS settings.

        Args
        ----
            config: Configuration to validate

        Returns
        -------
            List of validation errors
        """
        errors = []

        # Check required Supermicro settings
        required_settings = ["Boot_mode", "Secure_Boot"]
        for setting in required_settings:
            attribute = self._find_attribute(config, setting)
            if attribute is None:
                errors.append(f"Missing required Supermicro setting: {setting}")
            elif not attribute.text:
                errors.append(f"Empty value for Supermicro setting: {setting}")

        # Validate setting values
        boot_mode = self._find_attribute(config, "Boot_mode")
        if boot_mode is not None and boot_mode.text not in ["Legacy", "UEFI"]:
            errors.append(f"Invalid Supermicro Boot_mode value: {boot_mode.text}")

        secure_boot = self._find_attribute(config, "Secure_Boot")
        if secure_boot is not None and secure_boot.text not in ["Enabled", "Disabled"]:
            errors.append(f"Invalid Supermicro Secure_Boot value: {secure_boot.text}")

        return errors

    def get_sum_tool_settings(self) -> dict:
        """Get SUM (Supermicro Update Manager) specific settings.

        Returns
        -------
            Dictionary of SUM tool specific configuration
        """
        return {
            "sum_path": "/opt/sum/sum",
            "config_file_format": "txt",
            "requires_reboot": True,
            "supports_batch_mode": True,
        }
