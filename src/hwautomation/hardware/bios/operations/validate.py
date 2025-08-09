"""Validation operation handler for BIOS configuration.

This module handles validation of BIOS configurations including
structural validation, device compatibility checks, and rule validation.
"""

import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from ....logging import get_logger
from ..base import BaseOperationHandler, BiosConfigResult, ConfigMethod

logger = get_logger(__name__)


class ValidationOperationHandler(BaseOperationHandler):
    """Handles validation of BIOS configurations."""

    def __init__(self):
        """Initialize validation operation handler."""
        super().__init__()

    def execute(self, **kwargs) -> BiosConfigResult:
        """Execute validation operation on BIOS configuration.

        Args:
            **kwargs: Operation parameters including:
                - config: Configuration XML to validate
                - device_type: Target device type
                - device_mappings: Device mapping configuration
                - template_rules: Template rules configuration

        Returns:
            BiosConfigResult containing validation results
        """
        # Extract required parameters
        config = kwargs.get("config")
        device_type = kwargs.get("device_type", "")
        device_mappings = kwargs.get("device_mappings", {})
        template_rules = kwargs.get("template_rules", {})

        assert config is not None, "config parameter is required"
        assert device_type, "device_type parameter is required"

        self.logger.info(
            f"Validating BIOS configuration for device type: {device_type}"
        )

        errors = []

        try:
            # Structural validation
            errors.extend(self._validate_xml_structure(config))

            # Device compatibility validation
            errors.extend(
                self._validate_device_compatibility(
                    config, device_type, device_mappings
                )
            )

            # Template rules validation
            errors.extend(
                self._validate_template_rules(config, device_type, template_rules)
            )

            # Cross-validation between settings
            errors.extend(self._validate_setting_dependencies(config))

            # Value range validation
            errors.extend(self._validate_setting_values(config, device_type))

            if errors:
                self.logger.warning(f"Found {len(errors)} validation errors")
                return BiosConfigResult(
                    success=False,
                    method_used=ConfigMethod.REDFISH_STANDARD,
                    settings_applied={},
                    settings_failed={},
                    validation_errors=errors,
                )
            else:
                self.logger.info("Configuration validation passed")
                return BiosConfigResult(
                    success=True,
                    method_used=ConfigMethod.REDFISH_STANDARD,
                    settings_applied={},
                    settings_failed={},
                    validation_errors=[],
                )

        except Exception as e:
            self.logger.error(f"Error during validation: {e}")
            return BiosConfigResult(
                success=False,
                method_used=ConfigMethod.REDFISH_STANDARD,
                settings_applied={},
                settings_failed={},
                validation_errors=[f"Validation error: {e}"],
            )

    def validate_inputs(self, **kwargs) -> List[str]:
        """Validate input parameters for the validation operation.

        Args:
            **kwargs: Parameters including config, device_type

        Returns:
            List of validation errors
        """
        errors = []

        config = kwargs.get("config")
        device_type = kwargs.get("device_type")

        if config is None:
            errors.append("Missing required parameter: config")
        elif not isinstance(config, ET.Element):
            errors.append("config must be an XML Element")

        if not device_type:
            errors.append("Missing required parameter: device_type")
        elif not isinstance(device_type, str):
            errors.append("device_type must be a string")

        return errors

    def can_rollback(self) -> bool:
        """Check if validation operation supports rollback.

        Returns:
            False - validation operations don't support rollback
        """
        return False

    def _validate_xml_structure(self, config: ET.Element) -> List[str]:
        """Validate XML structure of the configuration.

        Args:
            config: Configuration XML

        Returns:
            List of structural validation errors
        """
        errors = []

        try:
            # Check root element
            if config.tag != "SystemConfiguration":
                errors.append(
                    f"Expected root element 'SystemConfiguration', got '{config.tag}'"
                )

            # Check for components
            components = config.findall(".//Component")
            if not components:
                errors.append("Configuration must contain at least one Component")

            # Validate each component
            for component in components:
                component_errors = self._validate_component_structure(component)
                errors.extend(component_errors)

        except Exception as e:
            errors.append(f"XML structure validation failed: {e}")

        return errors

    def _validate_component_structure(self, component: ET.Element) -> List[str]:
        """Validate structure of a single component.

        Args:
            component: Component element

        Returns:
            List of component validation errors
        """
        errors = []

        # Check FQDD attribute
        fqdd = component.get("FQDD")
        if not fqdd:
            errors.append("Component missing FQDD attribute")

        # Check for attributes
        attributes = component.findall(".//Attribute")
        if not attributes:
            errors.append(f"Component {fqdd} has no attributes")

        # Validate each attribute
        for attribute in attributes:
            name = attribute.get("Name")
            if not name:
                errors.append(f"Attribute in component {fqdd} missing Name")

            if attribute.text is None:
                errors.append(f"Attribute {name} in component {fqdd} has no value")

        return errors

    def _validate_device_compatibility(
        self, config: ET.Element, device_type: str, device_mappings: Dict[str, Any]
    ) -> List[str]:
        """Validate configuration compatibility with device type.

        Args:
            config: Configuration XML
            device_type: Target device type
            device_mappings: Device mapping configuration

        Returns:
            List of compatibility validation errors
        """
        errors = []

        if device_type not in device_mappings:
            errors.append(f"Unknown device type: {device_type}")
            return errors

        device_info = device_mappings[device_type]
        manufacturer = device_info.get("manufacturer", "").lower()

        # Manufacturer-specific validation
        if manufacturer == "dell":
            errors.extend(self._validate_dell_compatibility(config))
        elif manufacturer == "hpe":
            errors.extend(self._validate_hpe_compatibility(config))
        elif manufacturer == "supermicro":
            errors.extend(self._validate_supermicro_compatibility(config))

        return errors

    def _validate_dell_compatibility(self, config: ET.Element) -> List[str]:
        """Validate Dell-specific compatibility.

        Args:
            config: Configuration XML

        Returns:
            List of Dell compatibility errors
        """
        errors = []

        # Check for Dell-specific required settings
        required_dell_settings = ["BootMode", "SecureBoot"]
        for setting in required_dell_settings:
            if not self._find_attribute(config, setting):
                errors.append(f"Missing required Dell setting: {setting}")

        return errors

    def _validate_hpe_compatibility(self, config: ET.Element) -> List[str]:
        """Validate HPE-specific compatibility.

        Args:
            config: Configuration XML

        Returns:
            List of HPE compatibility errors
        """
        errors = []

        # Check for HPE-specific required settings
        required_hpe_settings = ["BootMode", "SecureBootStatus"]
        for setting in required_hpe_settings:
            if not self._find_attribute(config, setting):
                errors.append(f"Missing required HPE setting: {setting}")

        return errors

    def _validate_supermicro_compatibility(self, config: ET.Element) -> List[str]:
        """Validate Supermicro-specific compatibility.

        Args:
            config: Configuration XML

        Returns:
            List of Supermicro compatibility errors
        """
        errors = []

        # Check for Supermicro-specific required settings
        required_supermicro_settings = ["Boot_mode", "Secure_Boot"]
        for setting in required_supermicro_settings:
            if not self._find_attribute(config, setting):
                errors.append(f"Missing required Supermicro setting: {setting}")

        return errors

    def _validate_template_rules(
        self, config: ET.Element, device_type: str, template_rules: Dict[str, Any]
    ) -> List[str]:
        """Validate configuration against template rules.

        Args:
            config: Configuration XML
            device_type: Target device type
            template_rules: Template rules configuration

        Returns:
            List of template rule validation errors
        """
        errors: List[str] = []

        if device_type not in template_rules:
            # No specific rules for this device type
            return errors

        device_rules = template_rules[device_type]

        for setting_name, rule in device_rules.items():
            attribute = self._find_attribute(config, setting_name)

            if rule.get("action") == "required" and not attribute:
                errors.append(
                    f"Required setting '{setting_name}' missing for device type '{device_type}'"
                )

            if attribute and "allowed_values" in rule:
                allowed_values = rule["allowed_values"]
                if attribute.text not in allowed_values:
                    errors.append(
                        f"Invalid value '{attribute.text}' for setting '{setting_name}'. "
                        f"Allowed values: {allowed_values}"
                    )

        return errors

    def _validate_setting_dependencies(self, config: ET.Element) -> List[str]:
        """Validate dependencies between BIOS settings.

        Args:
            config: Configuration XML

        Returns:
            List of dependency validation errors
        """
        errors = []

        # Get all settings as a dictionary for easier access
        settings = {}
        for attribute in config.findall(".//Attribute"):
            name = attribute.get("Name")
            value = attribute.text
            if name and value:
                settings[name] = value

        # Validate common dependencies

        # SecureBoot requires UEFI boot mode
        secure_boot = (
            settings.get("SecureBoot")
            or settings.get("SecureBootStatus")
            or settings.get("Secure_Boot")
        )
        boot_mode = settings.get("BootMode") or settings.get("Boot_mode")

        if secure_boot == "Enabled" and boot_mode:
            if boot_mode.lower() not in ["uefi"]:
                errors.append("SecureBoot requires UEFI boot mode")

        # VT-d requires VT-x to be enabled
        vt_d = (
            settings.get("VtForDirectIo")
            or settings.get("IntelVtd")
            or settings.get("VT_d")
        )
        vt_x = settings.get("ProcVirtualization") or settings.get("VT_x")

        if vt_d == "Enabled" and vt_x != "Enabled":
            errors.append("VT-d requires processor virtualization (VT-x) to be enabled")

        return errors

    def _validate_setting_values(
        self, config: ET.Element, device_type: str
    ) -> List[str]:
        """Validate individual setting values.

        Args:
            config: Configuration XML
            device_type: Target device type

        Returns:
            List of value validation errors
        """
        errors = []

        # Common value validations
        common_validations = {
            "BootMode": ["Bios", "Uefi", "LegacyBios"],
            "SecureBoot": ["Enabled", "Disabled"],
            "SecureBootStatus": ["Enabled", "Disabled"],
            "Secure_Boot": ["Enabled", "Disabled"],
            "ProcVirtualization": ["Enabled", "Disabled"],
            "ProcHyperthreading": ["Enabled", "Disabled"],
            "Hyper_Threading": ["Enabled", "Disabled"],
            "VtForDirectIo": ["Enabled", "Disabled"],
            "IntelVtd": ["Enabled", "Disabled"],
            "VT_d": ["Enabled", "Disabled"],
            "VT_x": ["Enabled", "Disabled"],
        }

        for attribute in config.findall(".//Attribute"):
            name = attribute.get("Name")
            value = attribute.text

            if name in common_validations and value:
                valid_values = common_validations[name]
                if value not in valid_values:
                    errors.append(
                        f"Invalid value '{value}' for setting '{name}'. "
                        f"Valid values: {valid_values}"
                    )

        return errors

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
