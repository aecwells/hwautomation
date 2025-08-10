"""IPMI configuration operations.

This module handles IPMI configuration, vendor detection,
and system information gathering.
"""

import subprocess
import time
from typing import Dict, List, Optional

from hwautomation.logging import get_logger

from ..base import (
    BaseVendorHandler,
    IPMICommand,
    IPMICommandError,
    IPMIConfigResult,
    IPMICredentials,
    IPMISettings,
    IPMISystemInfo,
    IPMIVendor,
)

logger = get_logger(__name__)


class IPMIConfigurator:
    """Handles IPMI configuration operations."""

    def __init__(self, config: Optional[Dict] = None):
        """Initialize IPMI configurator.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.timeout = self.config.get("timeout", 30)
        self._vendor_handlers: Dict[IPMIVendor, BaseVendorHandler] = {}

    def detect_vendor(self, credentials: IPMICredentials) -> IPMIVendor:
        """Detect IPMI vendor for the target system.

        Args:
            credentials: IPMI connection credentials

        Returns:
            Detected vendor type
        """
        try:
            # Get system information to identify vendor
            result = self._execute_ipmi_command(credentials, IPMICommand.MC_INFO)

            if result.returncode != 0:
                logger.warning(f"MC info command failed: {result.stderr}")
                return IPMIVendor.UNKNOWN

            output = result.stdout.lower()

            # Vendor detection patterns
            if "supermicro" in output:
                return IPMIVendor.SUPERMICRO
            elif "hp" in output or "hewlett" in output or "ilo" in output:
                return IPMIVendor.HP_ILO
            elif "dell" in output or "idrac" in output:
                return IPMIVendor.DELL_IDRAC
            else:
                logger.info(f"Unknown vendor detected from output: {output[:200]}")
                return IPMIVendor.UNKNOWN

        except Exception as e:
            logger.error(f"Vendor detection failed: {e}")
            return IPMIVendor.UNKNOWN

    def configure_ipmi(
        self,
        credentials: IPMICredentials,
        settings: IPMISettings,
        vendor: Optional[IPMIVendor] = None,
    ) -> IPMIConfigResult:
        """Configure IPMI settings for the target system.

        Args:
            credentials: IPMI connection credentials
            settings: Configuration settings to apply
            vendor: Target vendor (auto-detected if not provided)

        Returns:
            Configuration result
        """
        start_time = time.time()

        if vendor is None:
            vendor = self.detect_vendor(credentials)

        logger.info(f"Configuring IPMI for vendor: {vendor.value}")

        try:
            # Get vendor-specific handler
            handler = self._get_vendor_handler(vendor)

            if handler:
                result = handler.configure_ipmi(credentials, settings)
            else:
                # Fall back to generic configuration
                result = self._configure_generic_ipmi(credentials, settings, vendor)

            result.execution_time = time.time() - start_time
            return result

        except Exception as e:
            logger.error(f"IPMI configuration failed: {e}")
            return IPMIConfigResult(
                success=False,
                vendor=vendor,
                errors=[str(e)],
                execution_time=time.time() - start_time,
            )

    def get_system_info(self, credentials: IPMICredentials) -> IPMISystemInfo:
        """Get system information for the target system.

        Args:
            credentials: IPMI connection credentials

        Returns:
            System information
        """
        try:
            # Get MC info
            mc_result = self._execute_ipmi_command(credentials, IPMICommand.MC_INFO)

            # Get FRU info
            fru_result = self._execute_ipmi_command(credentials, IPMICommand.FRU_LIST)

            return self._parse_system_info(mc_result.stdout, fru_result.stdout)

        except Exception as e:
            logger.error(f"Failed to get system info: {e}")
            return IPMISystemInfo()

    def validate_configuration(
        self,
        credentials: IPMICredentials,
        settings: IPMISettings,
    ) -> bool:
        """Validate IPMI configuration.

        Args:
            credentials: IPMI connection credentials
            settings: Settings to validate

        Returns:
            True if configuration is valid
        """
        try:
            # Basic connectivity test
            result = self._execute_ipmi_command(credentials, IPMICommand.MC_INFO)

            if result.returncode != 0:
                logger.error("Basic IPMI connectivity failed")
                return False

            # Vendor-specific validation
            vendor = self.detect_vendor(credentials)
            handler = self._get_vendor_handler(vendor)

            if handler:
                return handler.validate_configuration(credentials, settings)
            else:
                # Generic validation - just check connectivity
                return True

        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False

    def _get_vendor_handler(self, vendor: IPMIVendor) -> Optional[BaseVendorHandler]:
        """Get vendor-specific handler.

        Args:
            vendor: IPMI vendor

        Returns:
            Vendor handler or None if not available
        """
        if vendor not in self._vendor_handlers:
            try:
                # Lazy load vendor handlers
                if vendor == IPMIVendor.SUPERMICRO:
                    from ..vendors.supermicro import SupermicroHandler

                    self._vendor_handlers[vendor] = SupermicroHandler(vendor)
                elif vendor == IPMIVendor.HP_ILO:
                    from ..vendors.hp_ilo import HPiLOHandler

                    self._vendor_handlers[vendor] = HPiLOHandler(vendor)
                elif vendor == IPMIVendor.DELL_IDRAC:
                    from ..vendors.dell_idrac import DellHandler

                    self._vendor_handlers[vendor] = DellHandler(vendor)

            except ImportError as e:
                logger.warning(f"Vendor handler not available for {vendor.value}: {e}")
                return None

        return self._vendor_handlers.get(vendor)

    def _configure_generic_ipmi(
        self,
        credentials: IPMICredentials,
        settings: IPMISettings,
        vendor: IPMIVendor,
    ) -> IPMIConfigResult:
        """Generic IPMI configuration for unknown vendors.

        Args:
            credentials: IPMI connection credentials
            settings: Configuration settings
            vendor: Detected vendor

        Returns:
            Configuration result
        """
        result = IPMIConfigResult(success=True, vendor=vendor)

        try:
            # Basic password change
            if settings.admin_password:
                password_result = self._set_admin_password(
                    credentials, settings.admin_password
                )
                if password_result:
                    result.settings_applied.append("admin_password")
                else:
                    result.errors.append("Failed to set admin password")
                    result.success = False

        except Exception as e:
            result.errors.append(f"Generic configuration failed: {e}")
            result.success = False

        return result

    def _set_admin_password(
        self, credentials: IPMICredentials, new_password: str
    ) -> bool:
        """Set admin password via IPMI.

        Args:
            credentials: IPMI connection credentials
            new_password: New password to set

        Returns:
            True if successful
        """
        try:
            # Try user ID 2 (common admin user)
            result = self._execute_ipmi_command(
                credentials,
                f"user set password 2 {new_password}",
            )

            return result.returncode == 0

        except Exception as e:
            logger.error(f"Failed to set admin password: {e}")
            return False

    def _execute_ipmi_command(
        self,
        credentials: IPMICredentials,
        command: str,
    ) -> subprocess.CompletedProcess:
        """Execute an IPMI command.

        Args:
            credentials: IPMI connection credentials
            command: Command to execute

        Returns:
            Completed process result
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

    def _parse_system_info(self, mc_output: str, fru_output: str) -> IPMISystemInfo:
        """Parse system information from IPMI output.

        Args:
            mc_output: MC info command output
            fru_output: FRU list command output

        Returns:
            Parsed system information
        """
        info = IPMISystemInfo()

        # Parse MC info
        for line in mc_output.split("\n"):
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()

                if "manufacturer" in key:
                    info.manufacturer = value
                elif "product" in key:
                    info.product_name = value
                elif "firmware" in key or "version" in key:
                    info.firmware_version = value
                elif "guid" in key:
                    info.guid = value

        # Parse FRU info for additional details
        for line in fru_output.split("\n"):
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()

                if "serial" in key and not info.serial_number:
                    info.serial_number = value
                elif "manufacturer" in key and not info.manufacturer:
                    info.manufacturer = value

        # Detect vendor from manufacturer
        if info.manufacturer:
            manufacturer_lower = info.manufacturer.lower()
            if "supermicro" in manufacturer_lower:
                info.vendor = IPMIVendor.SUPERMICRO
            elif "hp" in manufacturer_lower or "hewlett" in manufacturer_lower:
                info.vendor = IPMIVendor.HP_ILO
            elif "dell" in manufacturer_lower:
                info.vendor = IPMIVendor.DELL_IDRAC

        return info
