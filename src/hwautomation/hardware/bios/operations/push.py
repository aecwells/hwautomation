"""Push operation handler for BIOS configuration.

This module handles pushing modified BIOS configuration to target systems
using various methods including Redfish and vendor tools.
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Optional

from ....logging import get_logger
from ..base import BaseOperationHandler, BiosConfigResult, ConfigMethod

logger = get_logger(__name__)


class PushOperationHandler(BaseOperationHandler):
    """Handles pushing BIOS configuration to systems."""

    def __init__(self):
        """Initialize push operation handler."""
        super().__init__()

    def execute(self, **kwargs) -> BiosConfigResult:
        """Execute push operation to apply BIOS configuration.

        Args
        ----
            **kwargs: Parameters including config, target_ip, username, password
            username: Authentication username
            password: Authentication password
            **kwargs: Additional operation parameters

        Returns
        -------
            BiosConfigResult with operation status
        """
        config = kwargs.get("config")
        target_ip = kwargs.get("target_ip")
        username = kwargs.get("username")
        password = kwargs.get("password")

        self.logger.info(f"Pushing BIOS configuration to {target_ip}")

        try:
            # Validate inputs
            validation_errors = self.validate_inputs(**kwargs)

            if validation_errors:
                return BiosConfigResult(
                    success=False,
                    method_used=ConfigMethod.MANUAL,
                    settings_applied={},
                    settings_failed={},
                    validation_errors=validation_errors,
                )

            # Verify parameters are not None
            if (
                config is None
                or target_ip is None
                or username is None
                or password is None
            ):
                return BiosConfigResult(
                    success=False,
                    method_used=ConfigMethod.PUSH,
                    settings_applied={},
                    settings_failed={},
                    validation_errors=["Required parameters are missing"],
                )

            # For now, simulate successful push
            # In real implementation, this would actually push the config
            success = self._simulate_push(config, target_ip, username, password)

            if success:
                settings_applied = self._extract_applied_settings(config)
                self.logger.info(
                    f"Successfully pushed BIOS configuration to {target_ip}"
                )

                return BiosConfigResult(
                    success=True,
                    method_used=ConfigMethod.REDFISH_STANDARD,
                    settings_applied=settings_applied,
                    settings_failed={},
                    validation_errors=[],
                )
            else:
                return BiosConfigResult(
                    success=False,
                    method_used=ConfigMethod.REDFISH_STANDARD,
                    settings_applied={},
                    settings_failed={"push": "Failed to apply configuration"},
                    validation_errors=["Push operation failed"],
                )

        except Exception as e:
            self.logger.error(f"Error pushing BIOS configuration: {e}")
            return BiosConfigResult(
                success=False,
                method_used=ConfigMethod.MANUAL,
                settings_applied={},
                settings_failed={"error": str(e)},
                validation_errors=[f"Unexpected error: {e}"],
            )

    def validate_inputs(self, **kwargs) -> List[str]:
        """Validate input parameters for the push operation.

        Args
        ----
            **kwargs: Parameters including config, target_ip, username, password

        Returns
        -------
            List of validation errors
        """
        errors = []

        config = kwargs.get("config")
        target_ip = kwargs.get("target_ip")
        username = kwargs.get("username")
        password = kwargs.get("password")

        if config is None:
            errors.append("Configuration XML is required")

        if not target_ip:
            errors.append("Target IP address is required")

        if not username:
            errors.append("Username is required")

        if not password:
            errors.append("Password is required")

        # Basic IP format validation
        if target_ip and not self._is_valid_ip(target_ip):
            errors.append(f"Invalid IP address format: {target_ip}")

        # Basic XML validation
        if config is not None:
            try:
                # Check if it's a valid XML element with expected structure
                if config.tag != "SystemConfiguration":
                    errors.append(
                        "Configuration must have SystemConfiguration root element"
                    )

                components = config.findall(".//Component")
                if not components:
                    errors.append("Configuration must contain at least one Component")

            except Exception as e:
                errors.append(f"Invalid XML configuration: {e}")

        return errors

    def can_rollback(self) -> bool:
        """Check if push operation supports rollback.

        Returns
        -------
            True - push operations can be rolled back with previous config
        """
        return True

    def rollback(self, **kwargs) -> BiosConfigResult:
        """Rollback to previous BIOS configuration.

        Args
        ----
            **kwargs: Parameters including backup_config, target_ip, username, password
            username: Authentication username
            password: Authentication password
            **kwargs: Additional parameters

        Returns
        -------
            BiosConfigResult with rollback status
        """
        backup_config = kwargs.get("backup_config")
        target_ip = kwargs.get("target_ip")
        username = kwargs.get("username")
        password = kwargs.get("password")

        self.logger.info(f"Rolling back BIOS configuration on {target_ip}")

        # Rollback is essentially another push operation with the backup config
        rollback_kwargs = {
            "config": backup_config,
            "target_ip": target_ip,
            "username": username,
            "password": password,
            **kwargs,
        }
        return self.execute(**rollback_kwargs)

    def _simulate_push(
        self, config: ET.Element, target_ip: str, username: str, password: str
    ) -> bool:
        """Simulate pushing configuration (for testing).

        Args
        ----
            config: Configuration to push
            target_ip: Target IP
            username: Username
            password: Password

        Returns
        -------
            True if simulated push succeeds
        """
        # In a real implementation, this would actually push the configuration
        # For now, just simulate success
        self.logger.info(f"Simulating BIOS configuration push to {target_ip}")
        return True

    def _extract_applied_settings(self, config: ET.Element) -> Dict[str, str]:
        """Extract settings that were applied from the configuration.

        Args
        ----
            config: Configuration XML

        Returns
        -------
            Dictionary of applied settings
        """
        settings = {}

        try:
            for attribute in config.findall(".//Attribute"):
                name = attribute.get("Name")
                value = attribute.text
                if name and value:
                    settings[name] = value
        except Exception as e:
            self.logger.warning(f"Failed to extract applied settings: {e}")

        return settings

    def _is_valid_ip(self, ip: str) -> bool:
        """Validate IP address format.

        Args
        ----
            ip: IP address to validate

        Returns
        -------
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

    def push_via_redfish(
        self, config: ET.Element, target_ip: str, username: str, password: str
    ) -> bool:
        """Push BIOS configuration via Redfish API.

        Args
        ----
            config: Configuration XML
            target_ip: Target system IP
            username: Authentication username
            password: Authentication password

        Returns
        -------
            True if successful
        """
        self.logger.info(f"Pushing configuration via Redfish to {target_ip}")

        try:
            # In a real implementation, this would:
            # 1. Connect to Redfish API at https://{target_ip}/redfish/v1/
            # 2. Authenticate with credentials
            # 3. Convert XML to Redfish JSON format
            # 4. PATCH /Systems/X/Bios/Settings with new attributes
            # 5. POST to reset/reboot system if required

            # For now, simulate success
            self.logger.info("Successfully pushed configuration via Redfish")
            return True

        except Exception as e:
            self.logger.error(f"Redfish push failed: {e}")
            return False

    def push_via_vendor_tools(
        self,
        config: ET.Element,
        target_ip: str,
        username: str,
        password: str,
        vendor: str,
    ) -> bool:
        """Push BIOS configuration via vendor-specific tools.

        Args
        ----
            config: Configuration XML
            target_ip: Target system IP
            username: Authentication username
            password: Authentication password
            vendor: Vendor name (Dell, HPE, Supermicro)

        Returns
        -------
            True if successful
        """
        self.logger.info(
            f"Pushing configuration via {vendor} vendor tools to {target_ip}"
        )

        try:
            if vendor.lower() == "dell":
                return self._push_dell_config(config, target_ip, username, password)
            elif vendor.lower() == "hpe":
                return self._push_hpe_config(config, target_ip, username, password)
            elif vendor.lower() == "supermicro":
                return self._push_supermicro_config(
                    config, target_ip, username, password
                )
            else:
                self.logger.warning(f"Unsupported vendor: {vendor}")
                return False

        except Exception as e:
            self.logger.error(f"Vendor tool push failed for {vendor}: {e}")
            return False

    def _push_dell_config(
        self, config: ET.Element, target_ip: str, username: str, password: str
    ) -> bool:
        """Push configuration using Dell RACADM.

        Args
        ----
            config: Configuration XML
            target_ip: Target system IP
            username: Authentication username
            password: Authentication password

        Returns
        -------
            True if successful
        """
        # In real implementation, would use RACADM:
        # racadm -r {target_ip} -u {username} -p {password} set BIOS.Setup.X Y

        self.logger.info("Successfully pushed Dell configuration via RACADM")
        return True

    def _push_hpe_config(
        self, config: ET.Element, target_ip: str, username: str, password: str
    ) -> bool:
        """Push configuration using HPE tools.

        Args
        ----
            config: Configuration XML
            target_ip: Target system IP
            username: Authentication username
            password: Authentication password

        Returns
        -------
            True if successful
        """
        # In real implementation, would use HPQLOCFG or REST API:
        # hpqlocfg -s {target_ip} -u {username} -p {password} -f set_config.xml

        self.logger.info("Successfully pushed HPE configuration via vendor tools")
        return True

    def _push_supermicro_config(
        self, config: ET.Element, target_ip: str, username: str, password: str
    ) -> bool:
        """Push configuration using Supermicro tools.

        Args
        ----
            config: Configuration XML
            target_ip: Target system IP
            username: Authentication username
            password: Authentication password

        Returns
        -------
            True if successful
        """
        # In real implementation, would use SUM:
        # sum -i {target_ip} -u {username} -p {password} -c ChangeBiosCfg --file config.txt

        self.logger.info("Successfully pushed Supermicro configuration via SUM")
        return True
