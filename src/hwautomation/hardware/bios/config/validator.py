"""Configuration validation for BIOS system.

This module provides validation capabilities for BIOS configurations,
template rules, and device mappings to ensure data integrity.
"""

import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from ....logging import get_logger

logger = get_logger(__name__)


class ConfigurationValidator:
    """Validates BIOS configuration data and rules."""
    
    def __init__(self, config_dir: str):
        """Initialize configuration validator.
        
        Args:
            config_dir: Directory containing BIOS configuration files
        """
        self.config_dir = config_dir
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    def validate_bios_xml(self, config: ET.Element) -> List[str]:
        """Validate BIOS configuration XML structure.
        
        Args:
            config: XML configuration to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        try:
            # Check if it's a valid XML element
            if config is None:
                errors.append("Configuration is None")
                return errors
            
            # Check root element
            if config.tag != 'SystemConfiguration':
                errors.append(f"Expected root element 'SystemConfiguration', got '{config.tag}'")
            
            # Check for required structure
            components = config.findall('.//Component')
            if not components:
                errors.append("No Component elements found in configuration")
            
            # Validate each component
            for component in components:
                component_errors = self._validate_component(component)
                errors.extend(component_errors)
            
        except Exception as e:
            errors.append(f"Error validating XML structure: {e}")
        
        return errors

    def validate_device_config(self, device_type: str, config: Dict[str, Any]) -> List[str]:
        """Validate device configuration.
        
        Args:
            device_type: Device type being validated
            config: Device configuration to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check required fields
        required_fields = ['manufacturer', 'model', 'motherboard']
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field '{field}' for device type '{device_type}'")
        
        # Validate manufacturer
        if 'manufacturer' in config:
            valid_manufacturers = ['Dell', 'HPE', 'Supermicro', 'Lenovo', 'Cisco']
            if config['manufacturer'] not in valid_manufacturers:
                errors.append(f"Unknown manufacturer '{config['manufacturer']}' for device type '{device_type}'")
        
        # Validate motherboard field
        if 'motherboard' in config:
            if not isinstance(config['motherboard'], list):
                errors.append(f"Motherboard field must be a list for device type '{device_type}'")
            elif not config['motherboard']:
                errors.append(f"Motherboard list cannot be empty for device type '{device_type}'")
        
        # Validate boolean fields
        boolean_fields = ['redfish_enabled', 'vendor_tools_available']
        for field in boolean_fields:
            if field in config and not isinstance(config[field], bool):
                errors.append(f"Field '{field}' must be boolean for device type '{device_type}'")
        
        return errors

    def validate_template_rules(self, device_type: str, rules: Dict[str, Any]) -> List[str]:
        """Validate template rules for a device type.
        
        Args:
            device_type: Device type being validated
            rules: Template rules to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if not isinstance(rules, dict):
            errors.append(f"Template rules for '{device_type}' must be a dictionary")
            return errors
        
        for setting_name, rule in rules.items():
            if not isinstance(rule, dict):
                errors.append(f"Rule '{setting_name}' for '{device_type}' must be a dictionary")
                continue
            
            # Validate required fields
            if 'action' not in rule:
                errors.append(f"Missing 'action' field in rule '{setting_name}' for '{device_type}'")
                continue
            
            # Validate action types
            valid_actions = ['set', 'preserve', 'conditional', 'delete', 'modify']
            if rule['action'] not in valid_actions:
                errors.append(f"Invalid action '{rule['action']}' in rule '{setting_name}' for '{device_type}'")
            
            # Validate action-specific requirements
            if rule['action'] == 'set' and 'value' not in rule:
                errors.append(f"Missing 'value' field for 'set' action in rule '{setting_name}' for '{device_type}'")
            
            if rule['action'] == 'conditional' and 'condition' not in rule:
                errors.append(f"Missing 'condition' field for 'conditional' action in rule '{setting_name}' for '{device_type}'")
        
        return errors

    def validate_preserve_settings(self, device_type: str, settings: List[str]) -> List[str]:
        """Validate preserve settings for a device type.
        
        Args:
            device_type: Device type being validated
            settings: List of settings to preserve
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if not isinstance(settings, list):
            errors.append(f"Preserve settings for '{device_type}' must be a list")
            return errors
        
        for setting in settings:
            if not isinstance(setting, str):
                errors.append(f"Preserve setting must be a string, got {type(setting)} for '{device_type}'")
            elif not setting.strip():
                errors.append(f"Empty preserve setting found for '{device_type}'")
        
        return errors

    def validate_setting_compatibility(self, setting_name: str, value: str, device_type: str) -> List[str]:
        """Validate if a setting is compatible with a device type.
        
        Args:
            setting_name: Name of the BIOS setting
            value: Value to set
            device_type: Target device type
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Device-specific validation rules
        if device_type.startswith('a1.'):  # Assume a1 devices are Dell
            errors.extend(self._validate_dell_setting(setting_name, value))
        elif device_type.startswith('d1.'):  # Assume d1 devices are HPE
            errors.extend(self._validate_hpe_setting(setting_name, value))
        
        return errors

    def _validate_component(self, component: ET.Element) -> List[str]:
        """Validate a single component element.
        
        Args:
            component: Component element to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check component has FQDD attribute
        fqdd = component.get('FQDD')
        if not fqdd:
            errors.append("Component missing FQDD attribute")
        
        # Check for attributes
        attributes = component.findall('.//Attribute')
        if not attributes:
            errors.append(f"Component {fqdd} has no attributes")
        
        # Validate each attribute
        for attribute in attributes:
            attr_errors = self._validate_attribute(attribute, fqdd)
            errors.extend(attr_errors)
        
        return errors

    def _validate_attribute(self, attribute: ET.Element, component_fqdd: str) -> List[str]:
        """Validate a single attribute element.
        
        Args:
            attribute: Attribute element to validate
            component_fqdd: FQDD of parent component
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Check attribute has Name
        name = attribute.get('Name')
        if not name:
            errors.append(f"Attribute in component {component_fqdd} missing Name")
        
        # Check attribute has value
        value = attribute.text
        if value is None:
            errors.append(f"Attribute {name} in component {component_fqdd} has no value")
        
        return errors

    def _validate_dell_setting(self, setting_name: str, value: str) -> List[str]:
        """Validate Dell-specific BIOS setting.
        
        Args:
            setting_name: Name of the setting
            value: Value to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Dell-specific validation rules
        dell_specific_settings = {
            'BootMode': ['Bios', 'Uefi'],
            'SecureBoot': ['Enabled', 'Disabled'],
            'ProcVirtualization': ['Enabled', 'Disabled']
        }
        
        if setting_name in dell_specific_settings:
            valid_values = dell_specific_settings[setting_name]
            if value not in valid_values:
                errors.append(f"Invalid value '{value}' for Dell setting '{setting_name}'. "
                              f"Valid values: {valid_values}")
        
        return errors

    def _validate_hpe_setting(self, setting_name: str, value: str) -> List[str]:
        """Validate HPE-specific BIOS setting.
        
        Args:
            setting_name: Name of the setting
            value: Value to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # HPE-specific validation rules
        hpe_specific_settings = {
            'BootMode': ['LegacyBios', 'Uefi'],
            'SecureBootStatus': ['Enabled', 'Disabled'],
            'ProcHyperthreading': ['Enabled', 'Disabled']
        }
        
        if setting_name in hpe_specific_settings:
            valid_values = hpe_specific_settings[setting_name]
            if value not in valid_values:
                errors.append(f"Invalid value '{value}' for HPE setting '{setting_name}'. "
                              f"Valid values: {valid_values}")
        
        return errors

    def cross_validate_settings(self, config: ET.Element) -> List[str]:
        """Perform cross-validation between related settings.
        
        Args:
            config: Configuration to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        try:
            # Get all attributes as a dictionary for easier validation
            settings = {}
            for attribute in config.findall('.//Attribute'):
                name = attribute.get('Name')
                value = attribute.text
                if name and value:
                    settings[name] = value
            
            # Cross-validation rules
            # Example: If SecureBoot is enabled, BootMode should be UEFI
            if settings.get('SecureBoot') == 'Enabled':
                boot_mode = settings.get('BootMode', '')
                if boot_mode.lower() not in ['uefi']:
                    errors.append("SecureBoot requires UEFI boot mode")
            
            # Example: Virtualization settings consistency
            vt_d = settings.get('VtForDirectIo', '')
            vt_x = settings.get('ProcVirtualization', '')
            if vt_d == 'Enabled' and vt_x != 'Enabled':
                errors.append("VT-d requires processor virtualization to be enabled")
            
        except Exception as e:
            errors.append(f"Error in cross-validation: {e}")
        
        return errors
