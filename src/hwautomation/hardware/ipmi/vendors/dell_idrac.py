"""Dell iDRAC-specific IPMI handler.

This module provides Dell iDRAC-specific IPMI configuration and management.
"""

import subprocess

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


class DellHandler(BaseVendorHandler):
    """Dell iDRAC-specific IPMI handler."""

    def __init__(self, vendor: IPMIVendor):
        """Initialize Dell iDRAC handler."""
        super().__init__(vendor)
        self.timeout = 30

    def detect_vendor(self, credentials: IPMICredentials) -> bool:
        """Detect if this is a Dell iDRAC system."""
        try:
            result = self._execute_command(credentials, IPMICommand.MC_INFO)
            output = result.stdout.lower()
            return "dell" in output or "idrac" in output
        except Exception:
            return False

    def configure_ipmi(
        self,
        credentials: IPMICredentials,
        settings: IPMISettings,
    ) -> IPMIConfigResult:
        """Configure IPMI settings for Dell iDRAC."""
        result = IPMIConfigResult(success=True, vendor=self.vendor)
        
        try:
            # Basic Dell iDRAC configuration
            if settings.admin_password:
                if self._set_admin_password(credentials, settings.admin_password):
                    result.settings_applied.append("admin_password")
                else:
                    result.errors.append("Failed to set admin password")
                    result.success = False

        except Exception as e:
            result.errors.append(f"Dell iDRAC configuration failed: {e}")
            result.success = False

        return result

    def get_system_info(self, credentials: IPMICredentials) -> IPMISystemInfo:
        """Get system information for Dell iDRAC."""
        info = IPMISystemInfo(vendor=self.vendor)
        
        try:
            result = self._execute_command(credentials, IPMICommand.MC_INFO)
            if result.returncode == 0:
                self._parse_mc_info(result.stdout, info)

        except Exception as e:
            logger.error(f"Failed to get Dell iDRAC system info: {e}")

        return info

    def validate_configuration(
        self,
        credentials: IPMICredentials,
        settings: IPMISettings,
    ) -> bool:
        """Validate IPMI configuration for Dell iDRAC."""
        try:
            result = self._execute_command(credentials, IPMICommand.MC_INFO)
            return result.returncode == 0
        except Exception:
            return False

    def _set_admin_password(self, credentials: IPMICredentials, password: str) -> bool:
        """Set admin password for Dell iDRAC."""
        try:
            result = self._execute_command(credentials, f"user set password 2 {password}")
            return result.returncode == 0
        except Exception:
            return False

    def _execute_command(self, credentials: IPMICredentials, command: str) -> subprocess.CompletedProcess:
        """Execute IPMI command."""
        cmd_args = [
            "ipmitool",
            "-I", credentials.interface,
            "-H", credentials.ip_address,
            "-U", credentials.username,
            "-P", credentials.password,
        ]
        
        cmd_args.extend(command.split())

        return subprocess.run(
            cmd_args,
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )

    def _parse_mc_info(self, output: str, info: IPMISystemInfo) -> None:
        """Parse MC info output."""
        for line in output.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower()
                value = value.strip()

                if 'manufacturer' in key:
                    info.manufacturer = value
                elif 'product' in key:
                    info.product_name = value
                elif 'firmware' in key:
                    info.firmware_version = value
