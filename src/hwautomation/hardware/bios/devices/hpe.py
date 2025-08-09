"""HPE device handler for BIOS configuration.

This module provides HPE-specific BIOS configuration handling including
iLO integration and vendor-specific settings.
"""

import xml.etree.ElementTree as ET
from typing import List

from ..base import BaseDeviceHandler, ConfigMethod, DeviceConfig
from ....logging import get_logger

logger = get_logger(__name__)


class HpeDeviceHandler(BaseDeviceHandler):
    """HPE-specific BIOS configuration handler."""
    
    def __init__(self, device_config: DeviceConfig):
        """Initialize HPE device handler.
        
        Args:
            device_config: HPE device configuration
        """
        super().__init__(device_config)
        self.hpe_specific_settings = {
            'BootMode': 'Uefi',
            'SecureBootStatus': 'Enabled',
            'ProcHyperthreading': 'Enabled',
            'ProcVirtualization': 'Enabled',
            'IntelVtd': 'Enabled'
        }

    def can_handle(self, device_type: str) -> bool:
        """Check if this handler can manage the given device type.
        
        Args:
            device_type: Device type to check
            
        Returns:
            True if this handler can manage the device type
        """
        # HPE devices typically use 'd1' prefix in our naming scheme
        return device_type.startswith('d1.') or self.device_config.manufacturer.lower() == 'hpe'

    def get_supported_methods(self) -> List[ConfigMethod]:
        """Get list of supported configuration methods for HPE devices.
        
        Returns:
            List of supported configuration methods
        """
        methods = []
        
        # HPE has good Redfish support via iLO
        if self.device_config.redfish_enabled:
            methods.append(ConfigMethod.REDFISH_STANDARD)
            methods.append(ConfigMethod.REDFISH_OEM)
        
        # HPE has vendor tools (HPQLOCFG, etc.)
        if self.device_config.vendor_tools_available:
            methods.append(ConfigMethod.VENDOR_TOOLS)
        
        # Hybrid approach combining Redfish and vendor tools
        if methods:
            methods.append(ConfigMethod.HYBRID)
        
        # Manual configuration always available as fallback
        methods.append(ConfigMethod.MANUAL)
        
        return methods

    def apply_device_specific_settings(self, config: ET.Element) -> ET.Element:
        """Apply HPE-specific BIOS settings.
        
        Args:
            config: Current configuration XML
            
        Returns:
            Modified configuration XML with HPE-specific settings
        """
        self.logger.info("Applying HPE-specific BIOS settings")
        
        try:
            # Apply HPE-specific settings
            for setting_name, setting_value in self.hpe_specific_settings.items():
                self._set_bios_attribute(config, setting_name, setting_value)
            
            # Apply device-type specific settings
            self._apply_device_type_settings(config)
            
            # Apply special handling if configured
            if self.device_config.special_handling:
                self._apply_special_handling(config)
            
            self.logger.info("Successfully applied HPE-specific settings")
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to apply HPE-specific settings: {e}")
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
            self.logger.debug(f"Updated HPE attribute {name} = {value}")
        else:
            # Create new attribute if it doesn't exist
            self._create_attribute(config, name, value)
            self.logger.debug(f"Created HPE attribute {name} = {value}")

    def _find_attribute(self, config: ET.Element, name: str) -> ET.Element:
        """Find an attribute by name in the configuration.
        
        Args:
            config: Configuration XML
            name: Attribute name to find
            
        Returns:
            Attribute element or None if not found
        """
        for attribute in config.findall('.//Attribute'):
            if attribute.get('Name') == name:
                return attribute
        return None

    def _create_attribute(self, config: ET.Element, name: str, value: str) -> None:
        """Create a new attribute in the configuration.
        
        Args:
            config: Configuration XML
            name: Attribute name
            value: Attribute value
        """
        # Find or create BIOS component (HPE uses different FQDD format)
        bios_component = None
        for component in config.findall('.//Component'):
            fqdd = component.get('FQDD', '')
            if 'BIOS' in fqdd or fqdd.startswith('System.'):
                bios_component = component
                break
        
        if bios_component is None:
            # Create BIOS component if it doesn't exist
            bios_component = ET.SubElement(config, 'Component')
            bios_component.set('FQDD', 'System.BIOS.1')
        
        # Create new attribute
        attribute = ET.SubElement(bios_component, 'Attribute')
        attribute.set('Name', name)
        attribute.text = value

    def _apply_device_type_settings(self, config: ET.Element) -> None:
        """Apply device-type specific settings for HPE devices.
        
        Args:
            config: Configuration XML
        """
        device_type = self.device_config.device_type
        
        # Apply settings based on device type patterns
        if '.c2.' in device_type:
            # Balanced performance settings for HPE
            self._set_bios_attribute(config, 'ProcAes', 'Enabled')
            self._set_bios_attribute(config, 'ProcTurbo', 'Enabled')
            
        elif '.c1.' in device_type:
            # Basic configuration settings for HPE
            self._set_bios_attribute(config, 'ProcAes', 'Enabled')
            self._set_bios_attribute(config, 'ProcTurbo', 'Auto')

    def _apply_special_handling(self, config: ET.Element) -> None:
        """Apply special handling configuration.
        
        Args:
            config: Configuration XML
        """
        special_handling = self.device_config.special_handling
        
        if 'custom_settings' in special_handling:
            custom_settings = special_handling['custom_settings']
            for setting_name, setting_value in custom_settings.items():
                self._set_bios_attribute(config, setting_name, setting_value)
                self.logger.debug(f"Applied custom HPE setting {setting_name} = {setting_value}")

    def get_priority(self) -> int:
        """Get priority for HPE device handler selection.
        
        Returns:
            Priority value (lower = higher priority)
        """
        return 20  # Medium-high priority for HPE devices

    def get_redfish_settings_map(self) -> dict:
        """Get mapping of BIOS settings to Redfish attribute names for HPE.
        
        Returns:
            Dictionary mapping BIOS setting names to Redfish paths
        """
        return {
            'BootMode': '/redfish/v1/Systems/1/Bios/Attributes/BootMode',
            'SecureBootStatus': '/redfish/v1/Systems/1/SecureBoot',
            'ProcHyperthreading': '/redfish/v1/Systems/1/Bios/Attributes/ProcHyperthreading',
            'ProcVirtualization': '/redfish/v1/Systems/1/Bios/Attributes/ProcVirtualization',
            'IntelVtd': '/redfish/v1/Systems/1/Bios/Attributes/IntelVtd'
        }

    def validate_hpe_specific_settings(self, config: ET.Element) -> List[str]:
        """Validate HPE-specific BIOS settings.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check required HPE settings
        required_settings = ['BootMode', 'SecureBootStatus']
        for setting in required_settings:
            attribute = self._find_attribute(config, setting)
            if attribute is None:
                errors.append(f"Missing required HPE setting: {setting}")
            elif not attribute.text:
                errors.append(f"Empty value for HPE setting: {setting}")
        
        # Validate setting values
        boot_mode = self._find_attribute(config, 'BootMode')
        if boot_mode is not None and boot_mode.text not in ['LegacyBios', 'Uefi']:
            errors.append(f"Invalid HPE BootMode value: {boot_mode.text}")
        
        secure_boot = self._find_attribute(config, 'SecureBootStatus')
        if secure_boot is not None and secure_boot.text not in ['Enabled', 'Disabled']:
            errors.append(f"Invalid HPE SecureBootStatus value: {secure_boot.text}")
        
        return errors

    def get_ilo_specific_settings(self) -> dict:
        """Get iLO-specific configuration settings.
        
        Returns:
            Dictionary of iLO-specific settings
        """
        return {
            'ilo_admin_name': 'Administrator',
            'ilo_security_state': 'Production',
            'ilo_fips_enable': 'Yes',
            'ilo_require_login_for_ilo_rbsu': 'Yes'
        }
