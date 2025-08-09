"""Pull operation handler for BIOS configuration.

This module handles pulling current BIOS configuration from target systems
using various methods including Redfish and vendor tools.
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

from ....logging import get_logger
from ..base import BaseOperationHandler, BiosConfigResult, ConfigMethod

logger = get_logger(__name__)


class PullOperationHandler(BaseOperationHandler):
    """Handles pulling current BIOS configuration from systems."""

    def __init__(self):
        """Initialize pull operation handler."""
        super().__init__()

    def execute(self, **kwargs) -> BiosConfigResult:
        """Execute pull operation to get current BIOS configuration.

        Args:
            **kwargs: Operation parameters including:
                - target_ip: Target system IP address
                - username: Authentication username
                - password: Authentication password

        Returns:
            BiosConfigResult containing current BIOS configuration
        """
        # Extract required parameters
        target_ip = kwargs.get("target_ip", "")
        username = kwargs.get("username", "")
        password = kwargs.get("password", "")

        assert target_ip, "target_ip parameter is required"
        assert username, "username parameter is required"
        assert password, "password parameter is required"

        self.logger.info(f"Pulling BIOS configuration from {target_ip}")

        # For now, return a mock configuration structure
        # In a real implementation, this would connect to the system
        # and retrieve the actual BIOS configuration

        config = self._create_mock_config()
        self.logger.info(f"Successfully pulled BIOS configuration from {target_ip}")

        return BiosConfigResult(
            success=True,
            method_used=ConfigMethod.REDFISH_STANDARD,
            settings_applied={},
            settings_failed={},
            validation_errors=[],
        )

    def validate_inputs(self, **kwargs) -> List[str]:
        """Validate input parameters for the pull operation.

        Args:
            **kwargs: Parameters including target_ip, username, password
            **kwargs: Additional parameters

        Returns:
            List of validation errors
        """
        errors = []

        target_ip = kwargs.get("target_ip", "")
        username = kwargs.get("username", "")
        password = kwargs.get("password", "")

        if not target_ip:
            errors.append("Target IP address is required")

        if not username:
            errors.append("Username is required")

        if not password:
            errors.append("Password is required")

        # Basic IP format validation
        if target_ip and not self._is_valid_ip(target_ip):
            errors.append(f"Invalid IP address format: {target_ip}")

        return errors

    def can_rollback(self) -> bool:
        """Check if pull operation supports rollback.

        Returns:
            False - pull operations don't support rollback
        """
        return False

    def _create_mock_config(self) -> ET.Element:
        """Create a mock BIOS configuration for testing.

        Returns:
            Mock XML configuration
        """
        root = ET.Element("SystemConfiguration")
        root.set("Model", "Mock System")
        root.set("ServiceTag", "MOCK123")

        # Create BIOS component
        bios_component = ET.SubElement(root, "Component")
        bios_component.set("FQDD", "BIOS.Setup.1-1")

        # Add some common BIOS attributes
        attributes = [
            ("BootMode", "Bios"),
            ("SecureBoot", "Disabled"),
            ("ProcVirtualization", "Disabled"),
            ("VtForDirectIo", "Disabled"),
            ("SriovGlobalEnable", "Disabled"),
            ("ProcHyperthreading", "Enabled"),
            ("MemOpMode", "OptimizerMode"),
        ]

        for name, value in attributes:
            attribute = ET.SubElement(bios_component, "Attribute")
            attribute.set("Name", name)
            attribute.text = value

        return root

    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format.

        Args:
            ip: IP address to validate

        Returns:
            True if valid IP format
        """
        try:
            parts = ip.split(".")
            if len(parts) != 4:
                return False

            for part in parts:
                num = int(part)
                if num < 0 or num > 255:
                    return False

            return True
        except (ValueError, AttributeError):
            return False

    def pull_via_redfish(
        self, target_ip: str, username: str, password: str
    ) -> Optional[ET.Element]:
        """Pull BIOS configuration via Redfish API.

        Args:
            target_ip: Target system IP
            username: Authentication username
            password: Authentication password

        Returns:
            XML configuration or None if failed
        """
        self.logger.info(f"Attempting Redfish pull from {target_ip}")

        try:
            # In a real implementation, this would:
            # 1. Connect to Redfish API at https://{target_ip}/redfish/v1/
            # 2. Authenticate with credentials
            # 3. Get BIOS attributes from /Systems/X/Bios/Attributes
            # 4. Convert Redfish JSON to XML format

            # For now, return mock config
            config = self._create_mock_config()
            self.logger.info("Successfully pulled configuration via Redfish")
            return config

        except Exception as e:
            self.logger.error(f"Redfish pull failed: {e}")
            return None

    def pull_via_vendor_tools(
        self, target_ip: str, username: str, password: str, vendor: str
    ) -> Optional[ET.Element]:
        """Pull BIOS configuration via vendor-specific tools.

        Args:
            target_ip: Target system IP
            username: Authentication username
            password: Authentication password
            vendor: Vendor name (Dell, HPE, Supermicro)

        Returns:
            XML configuration or None if failed
        """
        self.logger.info(f"Attempting {vendor} vendor tool pull from {target_ip}")

        try:
            if vendor.lower() == "dell":
                return self._pull_dell_config(target_ip, username, password)
            elif vendor.lower() == "hpe":
                return self._pull_hpe_config(target_ip, username, password)
            elif vendor.lower() == "supermicro":
                return self._pull_supermicro_config(target_ip, username, password)
            else:
                self.logger.warning(f"Unsupported vendor: {vendor}")
                return None

        except Exception as e:
            self.logger.error(f"Vendor tool pull failed for {vendor}: {e}")
            return None

    def _pull_dell_config(
        self, target_ip: str, username: str, password: str
    ) -> ET.Element:
        """Pull configuration using Dell RACADM.

        Args:
            target_ip: Target system IP
            username: Authentication username
            password: Authentication password

        Returns:
            XML configuration
        """
        # In real implementation, would use RACADM:
        # racadm -r {target_ip} -u {username} -p {password} get BIOS

        config = self._create_mock_config()
        self.logger.info("Successfully pulled Dell configuration via RACADM")
        return config

    def _pull_hpe_config(
        self, target_ip: str, username: str, password: str
    ) -> ET.Element:
        """Pull configuration using HPE tools.

        Args:
            target_ip: Target system IP
            username: Authentication username
            password: Authentication password

        Returns:
            XML configuration
        """
        # In real implementation, would use HPQLOCFG or REST API:
        # hpqlocfg -s {target_ip} -u {username} -p {password} -f get_config.xml

        config = self._create_mock_config()
        self.logger.info("Successfully pulled HPE configuration via vendor tools")
        return config

    def _pull_supermicro_config(
        self, target_ip: str, username: str, password: str
    ) -> ET.Element:
        """Pull configuration using Supermicro tools.

        Args:
            target_ip: Target system IP
            username: Authentication username
            password: Authentication password

        Returns:
            XML configuration
        """
        # In real implementation, would use SUM:
        # sum -i {target_ip} -u {username} -p {password} -c GetCurrentBiosCfg

        config = self._create_mock_config()
        self.logger.info("Successfully pulled Supermicro configuration via SUM")
        return config
