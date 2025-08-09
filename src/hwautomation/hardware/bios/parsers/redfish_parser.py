"""Redfish configuration parser for BIOS system.

This module provides parsing capabilities for Redfish/JSON-based BIOS
configuration formats used by modern systems.
"""

import json
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional

from ....logging import get_logger
from ..base import BaseConfigParser

logger = get_logger(__name__)


class RedfishConfigParser(BaseConfigParser):
    """Parser for Redfish/JSON-based BIOS configuration formats."""

    def __init__(self):
        """Initialize Redfish configuration parser."""
        super().__init__()

    def parse(self, data: str) -> ET.Element:
        """Parse Redfish JSON configuration data into XML Element.

        Args
        ----
            data: Redfish JSON configuration string

        Returns
        -------
            XML Element tree converted from JSON
        """
        try:
            # Parse JSON data
            json_data = json.loads(data)

            # Convert JSON to XML format
            xml_config = self._json_to_xml(json_data)

            self.logger.debug("Successfully parsed Redfish configuration")
            return xml_config

        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing error: {e}")
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error parsing Redfish data: {e}")
            raise

    def serialize(self, config: ET.Element) -> str:
        """Serialize XML Element to Redfish JSON format.

        Args
        ----
            config: XML Element to serialize

        Returns
        -------
            JSON string representation
        """
        try:
            # Convert XML to JSON structure
            json_data = self._xml_to_json(config)

            # Serialize to JSON string
            json_str = json.dumps(json_data, indent=2, sort_keys=True)

            self.logger.debug("Successfully serialized Redfish configuration")
            return json_str

        except Exception as e:
            self.logger.error(f"Error serializing to Redfish JSON: {e}")
            raise

    def _json_to_xml(self, json_data: Dict[str, Any]) -> ET.Element:
        """Convert Redfish JSON to XML format.

        Args
        ----
            json_data: Parsed JSON data

        Returns
        -------
            XML Element tree
        """
        # Create root element
        root = ET.Element("SystemConfiguration")

        # Set root attributes from JSON metadata
        if "Model" in json_data:
            root.set("Model", json_data["Model"])
        if "ServiceTag" in json_data:
            root.set("ServiceTag", json_data["ServiceTag"])

        # Create BIOS component
        bios_component = ET.SubElement(root, "Component")
        bios_component.set("FQDD", "BIOS.Setup.1-1")

        # Extract BIOS attributes from various possible JSON structures
        attributes = self._extract_bios_attributes(json_data)

        # Add attributes to component
        for name, value in attributes.items():
            attribute = ET.SubElement(bios_component, "Attribute")
            attribute.set("Name", name)
            attribute.text = str(value)

        return root

    def _extract_bios_attributes(self, json_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract BIOS attributes from Redfish JSON structure.

        Args
        ----
            json_data: Parsed JSON data

        Returns
        -------
            Dictionary of attribute name -> value pairs
        """
        attributes = {}

        # Try different possible JSON structures

        # Standard Redfish BIOS attributes location
        if "Attributes" in json_data:
            attributes.update(json_data["Attributes"])

        # Alternative structure: Bios.Attributes
        if "Bios" in json_data and "Attributes" in json_data["Bios"]:
            attributes.update(json_data["Bios"]["Attributes"])

        # OEM-specific structures
        if "Oem" in json_data:
            oem_data = json_data["Oem"]
            for vendor in ["Dell", "HPE", "Supermicro"]:
                if vendor in oem_data and "Attributes" in oem_data[vendor]:
                    attributes.update(oem_data[vendor]["Attributes"])

        # Direct attributes at root level
        for key, value in json_data.items():
            if key not in [
                "Model",
                "ServiceTag",
                "Bios",
                "Oem",
                "Attributes",
            ] and isinstance(value, (str, int, bool)):
                attributes[key] = str(value)

        return attributes

    def _xml_to_json(self, config: ET.Element) -> Dict[str, Any]:
        """Convert XML configuration to Redfish JSON format.

        Args
        ----
            config: XML configuration

        Returns
        -------
            JSON data structure
        """
        json_data: Dict[str, Any] = {}

        # Extract root attributes
        if config.get("Model"):
            json_data["Model"] = config.get("Model")
        if config.get("ServiceTag"):
            json_data["ServiceTag"] = config.get("ServiceTag")

        # Extract BIOS attributes
        attributes: Dict[str, Any] = {}
        for attribute in config.findall(".//Attribute"):
            name = attribute.get("Name")
            value = attribute.text
            if name and value is not None:
                # Try to convert to appropriate type
                try:
                    # Check if it's a boolean
                    if value.lower() in ["true", "false"]:
                        attributes[name] = value.lower() == "true"
                    # Check if it's a number
                    elif value.isdigit():
                        attributes[name] = int(value)
                    else:
                        attributes[name] = value
                except:
                    attributes[name] = value

        # Structure attributes in Redfish format
        json_data["Attributes"] = attributes

        return json_data

    def parse_redfish_response(self, response_data: str) -> Dict[str, Any]:
        """Parse a Redfish API response.

        Args
        ----
            response_data: JSON response from Redfish API

        Returns
        -------
            Parsed response data
        """
        try:
            response = json.loads(response_data)
            self.logger.debug("Successfully parsed Redfish response")
            return response
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing Redfish response: {e}")
            raise

    def create_redfish_patch_payload(self, settings: Dict[str, str]) -> str:
        """Create a Redfish PATCH payload for BIOS settings.

        Args
        ----
            settings: Dictionary of setting name -> value pairs

        Returns
        -------
            JSON string for PATCH request
        """
        try:
            payload = {"Attributes": settings}

            json_str = json.dumps(payload, indent=2)
            self.logger.debug(
                f"Created Redfish PATCH payload with {len(settings)} settings"
            )
            return json_str

        except Exception as e:
            self.logger.error(f"Error creating Redfish PATCH payload: {e}")
            raise

    def extract_redfish_urls(self, system_info: Dict[str, Any]) -> Dict[str, str]:
        """Extract relevant Redfish URLs from system information.

        Args
        ----
            system_info: System information from Redfish

        Returns
        -------
            Dictionary of URL names -> URLs
        """
        urls = {}

        try:
            # Extract common Redfish URLs
            if "Bios" in system_info:
                urls["bios"] = system_info["Bios"]["@odata.id"]

            if "Bios" in system_info and "Settings" in system_info["Bios"]:
                urls["bios_settings"] = system_info["Bios"]["Settings"]["@odata.id"]

            if "SecureBoot" in system_info:
                urls["secure_boot"] = system_info["SecureBoot"]["@odata.id"]

            if "Actions" in system_info:
                actions = system_info["Actions"]
                if "#ComputerSystem.Reset" in actions:
                    urls["reset"] = actions["#ComputerSystem.Reset"]["target"]

            self.logger.debug(f"Extracted {len(urls)} Redfish URLs")

        except Exception as e:
            self.logger.warning(f"Error extracting Redfish URLs: {e}")

        return urls

    def validate_redfish_structure(self, data: Dict[str, Any]) -> list:
        """Validate Redfish data structure.

        Args
        ----
            data: Redfish data to validate

        Returns
        -------
            List of validation errors
        """
        errors = []

        # Check for required Redfish elements
        if "@odata.type" not in data:
            errors.append("Missing @odata.type in Redfish response")

        if "@odata.id" not in data:
            errors.append("Missing @odata.id in Redfish response")

        # Check for BIOS-specific structure
        if "Attributes" in data:
            if not isinstance(data["Attributes"], dict):
                errors.append("Attributes field must be a dictionary")

        return errors
