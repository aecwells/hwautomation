"""XML configuration parser for BIOS system.

This module provides parsing capabilities for XML-based BIOS configuration
formats used by various vendors.
"""

import xml.etree.ElementTree as ET
from typing import Optional

from ....logging import get_logger
from ..base import BaseConfigParser

logger = get_logger(__name__)


class XmlConfigParser(BaseConfigParser):
    """Parser for XML-based BIOS configuration formats."""

    def __init__(self):
        """Initialize XML configuration parser."""
        super().__init__()

    def parse(self, data: str) -> ET.Element:
        """Parse XML configuration data into XML Element.

        Args:
            data: XML configuration string

        Returns:
            XML Element tree
        """
        try:
            # Parse the XML string
            root = ET.fromstring(data)
            self.logger.debug("Successfully parsed XML configuration")
            return root

        except ET.ParseError as e:
            self.logger.error(f"XML parsing error: {e}")
            raise ValueError(f"Invalid XML format: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error parsing XML: {e}")
            raise

    def serialize(self, config: ET.Element) -> str:
        """Serialize XML Element to string format.

        Args:
            config: XML Element to serialize

        Returns:
            XML string representation
        """
        try:
            # Add proper indentation for readability
            ET.indent(config, space="  ")

            # Convert to string with XML declaration
            xml_str = ET.tostring(config, encoding="unicode", xml_declaration=True)

            self.logger.debug("Successfully serialized XML configuration")
            return xml_str

        except Exception as e:
            self.logger.error(f"Error serializing XML: {e}")
            raise

    def validate_xml_structure(self, config: ET.Element) -> list:
        """Validate XML structure for BIOS configuration.

        Args:
            config: XML Element to validate

        Returns:
            List of validation errors
        """
        errors = []

        try:
            # Check root element
            if config.tag != "SystemConfiguration":
                errors.append(
                    f"Expected root element 'SystemConfiguration', got '{config.tag}'"
                )

            # Check for required attributes
            required_attrs = ["Model", "ServiceTag"]
            for attr in required_attrs:
                if attr not in config.attrib:
                    errors.append(
                        f"Missing required attribute '{attr}' in root element"
                    )

            # Check for components
            components = config.findall(".//Component")
            if not components:
                errors.append("No Component elements found")

            # Validate component structure
            for component in components:
                component_errors = self._validate_component(component)
                errors.extend(component_errors)

        except Exception as e:
            errors.append(f"Error validating XML structure: {e}")

        return errors

    def _validate_component(self, component: ET.Element) -> list:
        """Validate a single component element.

        Args:
            component: Component element to validate

        Returns:
            List of validation errors for this component
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

        # Validate attributes
        for attribute in attributes:
            name = attribute.get("Name")
            if not name:
                errors.append(f"Attribute in component {fqdd} missing Name")

            if attribute.text is None:
                errors.append(f"Attribute {name} in component {fqdd} has no value")

        return errors

    def extract_bios_settings(self, config: ET.Element) -> dict:
        """Extract BIOS settings from XML configuration.

        Args:
            config: XML configuration

        Returns:
            Dictionary of BIOS setting name -> value pairs
        """
        settings = {}

        try:
            for attribute in config.findall(".//Attribute"):
                name = attribute.get("Name")
                value = attribute.text
                if name and value is not None:
                    settings[name] = value

            self.logger.debug(f"Extracted {len(settings)} BIOS settings from XML")

        except Exception as e:
            self.logger.error(f"Error extracting BIOS settings: {e}")

        return settings

    def update_bios_setting(
        self, config: ET.Element, setting_name: str, setting_value: str
    ) -> bool:
        """Update a BIOS setting in the XML configuration.

        Args:
            config: XML configuration to update
            setting_name: Name of the setting to update
            setting_value: New value for the setting

        Returns:
            True if setting was updated, False otherwise
        """
        try:
            # Find the attribute
            for attribute in config.findall(".//Attribute"):
                if attribute.get("Name") == setting_name:
                    attribute.text = setting_value
                    self.logger.debug(
                        f"Updated setting {setting_name} = {setting_value}"
                    )
                    return True

            # Setting not found
            self.logger.warning(f"Setting {setting_name} not found in configuration")
            return False

        except Exception as e:
            self.logger.error(f"Error updating BIOS setting {setting_name}: {e}")
            return False

    def create_bios_setting(
        self,
        config: ET.Element,
        component_fqdd: str,
        setting_name: str,
        setting_value: str,
    ) -> bool:
        """Create a new BIOS setting in the XML configuration.

        Args:
            config: XML configuration
            component_fqdd: FQDD of the component to add setting to
            setting_name: Name of the new setting
            setting_value: Value for the new setting

        Returns:
            True if setting was created, False otherwise
        """
        try:
            # Find the component
            component = None
            for comp in config.findall(".//Component"):
                if comp.get("FQDD") == component_fqdd:
                    component = comp
                    break

            if component is None:
                # Create component if it doesn't exist
                component = ET.SubElement(config, "Component")
                component.set("FQDD", component_fqdd)

            # Create new attribute
            attribute = ET.SubElement(component, "Attribute")
            attribute.set("Name", setting_name)
            attribute.text = setting_value

            self.logger.debug(
                f"Created setting {setting_name} = {setting_value} in {component_fqdd}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error creating BIOS setting {setting_name}: {e}")
            return False

    def merge_configurations(
        self, base_config: ET.Element, overlay_config: ET.Element
    ) -> ET.Element:
        """Merge two XML configurations, with overlay taking precedence.

        Args:
            base_config: Base configuration
            overlay_config: Configuration to overlay on base

        Returns:
            Merged configuration
        """
        try:
            # Create a copy of the base configuration
            import copy

            merged_config = copy.deepcopy(base_config)

            # Extract settings from overlay
            overlay_settings = self.extract_bios_settings(overlay_config)

            # Apply overlay settings to merged config
            for setting_name, setting_value in overlay_settings.items():
                self.update_bios_setting(merged_config, setting_name, setting_value)

            self.logger.debug(
                f"Merged configurations with {len(overlay_settings)} overlay settings"
            )
            return merged_config

        except Exception as e:
            self.logger.error(f"Error merging configurations: {e}")
            raise
