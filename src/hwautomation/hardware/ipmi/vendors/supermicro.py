"""Supermicro-specific IPMI handler.

This module provides Supermicro-specific IPMI configuration and management.
"""

import subprocess
from typing import List

from hwautomation.logging import get_logger

from ..base import (
    BaseVendorHandler,
    IPMICommand,
    IPMIConfigResult,
    IPMICredentials,
    IPMISettings,
    IPMISystemInfo,
    IPMIVendor,
)

logger = get_logger(__name__)


class SupermicroHandler(BaseVendorHandler):
    """Supermicro-specific IPMI handler."""

    def __init__(self, vendor: IPMIVendor):
        """Initialize Supermicro handler."""
        super().__init__(vendor)
        self.timeout = 30

    def detect_vendor(self, credentials: IPMICredentials) -> bool:
        """Detect if this is a Supermicro system.

        Args:
            credentials: IPMI credentials for detection

        Returns:
            True if this is a Supermicro system
        """
        try:
            result = self._execute_command(credentials, IPMICommand.MC_INFO)
            output = result.stdout.lower()
            return "supermicro" in output
        except Exception:
            return False

    def configure_ipmi(
        self,
        credentials: IPMICredentials,
        settings: IPMISettings,
    ) -> IPMIConfigResult:
        """Configure IPMI settings for Supermicro.

        Args:
            credentials: IPMI connection credentials
            settings: Configuration settings to apply

        Returns:
            Configuration result
        """
        result = IPMIConfigResult(success=True, vendor=self.vendor)

        try:
            # Configure KCS control
            if settings.kcs_control:
                if self._configure_kcs_control(credentials, settings.kcs_control):
                    result.settings_applied.append("kcs_control")
                else:
                    result.errors.append("Failed to configure KCS control")

            # Configure host interface
            if settings.host_interface:
                if self._configure_host_interface(credentials, settings.host_interface):
                    result.settings_applied.append("host_interface")
                else:
                    result.errors.append("Failed to configure host interface")

            # Set admin password
            if settings.admin_password:
                if self._set_admin_password(credentials, settings.admin_password):
                    result.settings_applied.append("admin_password")
                else:
                    result.errors.append("Failed to set admin password")
                    result.success = False

            if result.errors:
                result.success = len(result.settings_applied) > 0

        except Exception as e:
            result.errors.append(f"Supermicro configuration failed: {e}")
            result.success = False

        return result

    def get_system_info(self, credentials: IPMICredentials) -> IPMISystemInfo:
        """Get system information for Supermicro.

        Args:
            credentials: IPMI connection credentials

        Returns:
            System information
        """
        info = IPMISystemInfo(vendor=self.vendor)

        try:
            # Get MC info
            result = self._execute_command(credentials, IPMICommand.MC_INFO)
            if result.returncode == 0:
                self._parse_mc_info(result.stdout, info)

            # Get FRU info
            result = self._execute_command(credentials, IPMICommand.FRU_LIST)
            if result.returncode == 0:
                self._parse_fru_info(result.stdout, info)

        except Exception as e:
            logger.error(f"Failed to get Supermicro system info: {e}")

        return info

    def validate_configuration(
        self,
        credentials: IPMICredentials,
        settings: IPMISettings,
    ) -> bool:
        """Validate IPMI configuration for Supermicro.

        Args:
            credentials: IPMI connection credentials
            settings: Settings to validate

        Returns:
            True if configuration is valid
        """
        try:
            # Basic connectivity test
            result = self._execute_command(credentials, IPMICommand.MC_INFO)
            if result.returncode != 0:
                return False

            # TODO: Add Supermicro-specific validation checks

            return True

        except Exception as e:
            logger.error(f"Supermicro validation failed: {e}")
            return False

    def _configure_kcs_control(
        self, credentials: IPMICredentials, control: str
    ) -> bool:
        """Configure KCS control for Supermicro.

        Args:
            credentials: IPMI credentials
            control: Control setting ('user' or 'system')

        Returns:
            True if successful
        """
        try:
            # Supermicro-specific KCS configuration
            command = (
                f"raw 0x30 0x70 0x0c 0x01 0x01"
                if control == "user"
                else f"raw 0x30 0x70 0x0c 0x01 0x00"
            )
            result = self._execute_command(credentials, command)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to configure KCS control: {e}")
            return False

    def _configure_host_interface(
        self, credentials: IPMICredentials, interface: str
    ) -> bool:
        """Configure host interface for Supermicro.

        Args:
            credentials: IPMI credentials
            interface: Interface setting ('on' or 'off')

        Returns:
            True if successful
        """
        try:
            # Supermicro-specific host interface configuration
            command = (
                f"raw 0x30 0x70 0x0c 0x02 0x00"
                if interface == "off"
                else f"raw 0x30 0x70 0x0c 0x02 0x01"
            )
            result = self._execute_command(credentials, command)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to configure host interface: {e}")
            return False

    def _set_admin_password(self, credentials: IPMICredentials, password: str) -> bool:
        """Set admin password for Supermicro.

        Args:
            credentials: IPMI credentials
            password: New password

        Returns:
            True if successful
        """
        try:
            result = self._execute_command(
                credentials, f"user set password 2 {password}"
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to set admin password: {e}")
            return False

    def _execute_command(
        self, credentials: IPMICredentials, command: str
    ) -> subprocess.CompletedProcess:
        """Execute IPMI command.

        Args:
            credentials: IPMI credentials
            command: Command to execute

        Returns:
            Completed process
        """
        cmd_args = [
            "ipmitool",
            "-I",
            credentials.interface,
            "-H",
            credentials.ip_address,
            "-U",
            credentials.username,
            "-P",
            credentials.password,
        ]

        cmd_args.extend(command.split())

        return subprocess.run(
            cmd_args,
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )

    def _parse_mc_info(self, output: str, info: IPMISystemInfo) -> None:
        """Parse MC info output.

        Args:
            output: MC info output
            info: System info object to populate
        """
        for line in output.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()

                if "manufacturer" in key:
                    info.manufacturer = value
                elif "product" in key:
                    info.product_name = value
                elif "firmware" in key:
                    info.firmware_version = value

    def _parse_fru_info(self, output: str, info: IPMISystemInfo) -> None:
        """Parse FRU info output.

        Args:
            output: FRU info output
            info: System info object to populate
        """
        for line in output.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()

                if "serial" in key and not info.serial_number:
                    info.serial_number = value
