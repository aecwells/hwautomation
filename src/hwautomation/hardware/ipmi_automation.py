"""
IPMI Automation Service

Implements automated IPMI configuration based on BMC boarding process requirements.
Handles different server types (Supermicro, HP iLO) with vendor-specific settings.
."""

import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from hwautomation.logging import get_logger
from ..utils.network import SSHClient

logger = get_logger(__name__)


class IPMIVendor(Enum):
    """Supported IPMI vendors."""

    SUPERMICRO = "supermicro"
    HP_ILO = "hp_ilo"
    DELL_IDRAC = "dell_idrac"
    UNKNOWN = "unknown"


@dataclass
class IPMISettings:
    """IPMI configuration settings."""

    admin_password: str
    kcs_control: Optional[str] = None  # 'user' for Supermicro
    host_interface: Optional[str] = None  # 'off' for Supermicro
    ipmi_over_lan: Optional[str] = None  # 'enabled' for HP
    require_host_auth: Optional[str] = None  # 'enabled' for HP
    require_login_rbsu: Optional[str] = None  # 'enabled' for HP
    oob_license_required: bool = True


@dataclass
class IPMIConfigResult:
    """Result of IPMI configuration attempt."""

    success: bool
    vendor: IPMIVendor
    firmware_version: Optional[str] = None
    settings_applied: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class IPMIAutomationService:
    """Service for automating IPMI configuration according to BMC boarding requirements."""

    def __init__(self, config: Dict = None):
        """
        Initialize IPMI automation service

        Args:
            config: Configuration dictionary
        ."""
        self.config = config or {}
        self.default_passwords = {
            IPMIVendor.SUPERMICRO: self.config.get("ipmi_default_password", "ADMIN"),
            IPMIVendor.HP_ILO: self.config.get("ipmi_default_password", "ADMIN"),
        }

    def detect_ipmi_vendor(
        self, ipmi_ip: str, username: str = "ADMIN", password: str = "ADMIN"
    ) -> IPMIVendor:
        """
        Detect IPMI vendor based on system responses

        Args:
            ipmi_ip: IPMI IP address
            username: IPMI username
            password: IPMI password

        Returns:
            Detected IPMI vendor
        ."""
        try:
            # Try to get MC info to detect vendor
            cmd = [
                "ipmitool",
                "-I",
                "lanplus",
                "-H",
                ipmi_ip,
                "-U",
                username,
                "-P",
                password,
                "mc",
                "info",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                output = result.stdout.lower()
                if "supermicro" in output:
                    return IPMIVendor.SUPERMICRO
                elif "hewlett" in output or "hp" in output or "ilo" in output:
                    return IPMIVendor.HP_ILO
                elif "dell" in output:
                    return IPMIVendor.DELL_IDRAC

            # Try manufacturer-specific commands
            # Try Supermicro-specific command
            cmd = [
                "ipmitool",
                "-I",
                "lanplus",
                "-H",
                ipmi_ip,
                "-U",
                username,
                "-P",
                password,
                "raw",
                "0x30",
                "0x21",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return IPMIVendor.SUPERMICRO

        except Exception as e:
            logger.warning(f"Error detecting IPMI vendor for {ipmi_ip}: {e}")

        return IPMIVendor.UNKNOWN

    def configure_supermicro_ipmi(
        self, ipmi_ip: str, settings: IPMISettings
    ) -> IPMIConfigResult:
        """
        Configure Supermicro IPMI according to BMC boarding requirements

        Based on the boarding document:
        - Change ADMIN password to default
        - Set KCS control to 'user' (disables OS access)
        - Disable Host Interface (device must be powered off)
        - Ensure OOB license is activated
        ."""
        result = IPMIConfigResult(
            success=False,
            vendor=IPMIVendor.SUPERMICRO,
            settings_applied=[],
            errors=[],
            warnings=[],
        )

        try:
            # Step 1: Change admin password
            logger.info(f"Configuring Supermicro IPMI at {ipmi_ip}")

            # First try with default credentials to change password
            cmd = [
                "ipmitool",
                "-I",
                "lanplus",
                "-H",
                ipmi_ip,
                "-U",
                "ADMIN",
                "-P",
                "ADMIN",
                "user",
                "set",
                "password",
                "2",
                settings.admin_password,
            ]

            result_cmd = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result_cmd.returncode == 0:
                result.settings_applied.append("Admin password updated")
                logger.info("Admin password updated successfully")
            else:
                # Try with current password if default failed
                cmd = [
                    "ipmitool",
                    "-I",
                    "lanplus",
                    "-H",
                    ipmi_ip,
                    "-U",
                    "ADMIN",
                    "-P",
                    settings.admin_password,
                    "user",
                    "set",
                    "password",
                    "2",
                    settings.admin_password,
                ]
                result_cmd = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=10
                )
                if result_cmd.returncode != 0:
                    result.errors.append("Failed to set admin password")
                    return result

            # Step 2: Get firmware version
            cmd = [
                "ipmitool",
                "-I",
                "lanplus",
                "-H",
                ipmi_ip,
                "-U",
                "ADMIN",
                "-P",
                settings.admin_password,
                "mc",
                "info",
            ]
            result_cmd = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result_cmd.returncode == 0:
                for line in result_cmd.stdout.split("\n"):
                    if "Firmware Revision" in line:
                        result.firmware_version = line.split(":")[-1].strip()
                        break

            # Step 3: Configure KCS control (if specified)
            if settings.kcs_control:
                # This requires vendor-specific commands or web interface access
                # For now, we'll log it as requiring manual configuration
                result.warnings.append(
                    f"KCS control setting to '{settings.kcs_control}' requires manual configuration via web interface"
                )

            # Step 4: Configure Host Interface (if specified)
            if settings.host_interface:
                # This also requires vendor-specific configuration
                result.warnings.append(
                    f"Host interface setting to '{settings.host_interface}' requires manual configuration via web interface"
                )

            # Step 5: Check OOB license status
            if settings.oob_license_required:
                # Try to run a command that requires OOB license
                cmd = [
                    "ipmitool",
                    "-I",
                    "lanplus",
                    "-H",
                    ipmi_ip,
                    "-U",
                    "ADMIN",
                    "-P",
                    settings.admin_password,
                    "fru",
                    "list",
                ]
                result_cmd = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=10
                )
                if result_cmd.returncode == 0:
                    result.settings_applied.append("OOB license appears to be active")
                else:
                    result.warnings.append(
                        "OOB license may not be activated - some functions may be limited"
                    )

            # Step 6: Verify basic IPMI functionality
            cmd = [
                "ipmitool",
                "-I",
                "lanplus",
                "-H",
                ipmi_ip,
                "-U",
                "ADMIN",
                "-P",
                settings.admin_password,
                "power",
                "status",
            ]
            result_cmd = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result_cmd.returncode == 0:
                result.settings_applied.append("IPMI power control verified")
                result.success = True
            else:
                result.errors.append("IPMI power control verification failed")

        except subprocess.TimeoutExpired:
            result.errors.append("IPMI configuration timeout")
        except Exception as e:
            result.errors.append(f"IPMI configuration error: {e}")

        return result

    def configure_hp_ilo_ipmi(
        self, ipmi_ip: str, settings: IPMISettings
    ) -> IPMIConfigResult:
        """
        Configure HP iLO IPMI according to BMC boarding requirements

        Based on the boarding document:
        - Set IPMI/DCMI over LAN to ENABLED
        - Set Require Host Authentication to ENABLED
        - Set Require Login for iLO RBSU to ENABLED
        - Create ADMIN user with default password
        ."""
        result = IPMIConfigResult(
            success=False,
            vendor=IPMIVendor.HP_ILO,
            settings_applied=[],
            errors=[],
            warnings=[],
        )

        try:
            logger.info(f"Configuring HP iLO at {ipmi_ip}")

            # Step 1: Test connectivity and get info
            cmd = [
                "ipmitool",
                "-I",
                "lanplus",
                "-H",
                ipmi_ip,
                "-U",
                "Administrator",
                "-P",
                "admin",
                "mc",
                "info",
            ]
            result_cmd = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result_cmd.returncode != 0:
                # Try with ADMIN user
                cmd = [
                    "ipmitool",
                    "-I",
                    "lanplus",
                    "-H",
                    ipmi_ip,
                    "-U",
                    "ADMIN",
                    "-P",
                    settings.admin_password,
                    "mc",
                    "info",
                ]
                result_cmd = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=10
                )

            if result_cmd.returncode == 0:
                for line in result_cmd.stdout.split("\n"):
                    if "Firmware Revision" in line:
                        result.firmware_version = line.split(":")[-1].strip()
                        break
                result.settings_applied.append("iLO connectivity verified")
            else:
                result.errors.append("Failed to connect to iLO")
                return result

            # Step 2: Enable IPMI over LAN (this typically requires web interface or SSH)
            result.warnings.append(
                "IPMI/DCMI over LAN setting requires configuration via iLO web interface"
            )

            # Step 3: Configure authentication settings (requires web interface)
            result.warnings.append(
                "Host authentication and RBSU login settings require configuration via iLO web interface"
            )

            # Step 4: Verify power control
            cmd = [
                "ipmitool",
                "-I",
                "lanplus",
                "-H",
                ipmi_ip,
                "-U",
                "ADMIN",
                "-P",
                settings.admin_password,
                "power",
                "status",
            ]
            result_cmd = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result_cmd.returncode == 0:
                result.settings_applied.append("IPMI power control verified")
                result.success = True
            else:
                result.errors.append("IPMI power control verification failed")

        except subprocess.TimeoutExpired:
            result.errors.append("iLO configuration timeout")
        except Exception as e:
            result.errors.append(f"iLO configuration error: {e}")

        return result

    def configure_ipmi(
        self, ipmi_ip: str, device_type: str, admin_password: str = None
    ) -> IPMIConfigResult:
        """
        Configure IPMI based on device type and vendor detection

        Args:
            ipmi_ip: IPMI IP address
            device_type: BMC device type
            admin_password: Admin password to set

        Returns:
            IPMIConfigResult with configuration results
        ."""
        if admin_password is None:
            admin_password = self.config.get("ipmi_default_password", "ADMIN")

        # Detect vendor
        vendor = self.detect_ipmi_vendor(ipmi_ip)
        logger.info(f"Detected IPMI vendor: {vendor} for {ipmi_ip}")

        # Create settings based on device type and vendor
        settings = self._create_ipmi_settings(device_type, vendor, admin_password)

        # Configure based on vendor
        if vendor == IPMIVendor.SUPERMICRO:
            return self.configure_supermicro_ipmi(ipmi_ip, settings)
        elif vendor == IPMIVendor.HP_ILO:
            return self.configure_hp_ilo_ipmi(ipmi_ip, settings)
        else:
            # Generic IPMI configuration
            return self._configure_generic_ipmi(ipmi_ip, settings)

    def _create_ipmi_settings(
        self, device_type: str, vendor: IPMIVendor, admin_password: str
    ) -> IPMISettings:
        """Create IPMI settings based on device type and vendor."""
        settings = IPMISettings(admin_password=admin_password)

        if vendor == IPMIVendor.SUPERMICRO:
            # Supermicro settings from boarding document
            settings.kcs_control = "user"
            settings.host_interface = "off"
            settings.oob_license_required = True

        elif vendor == IPMIVendor.HP_ILO:
            # HP iLO settings from boarding document
            settings.ipmi_over_lan = "enabled"
            settings.require_host_auth = "enabled"
            settings.require_login_rbsu = "enabled"
            settings.oob_license_required = False

        return settings

    def _configure_generic_ipmi(
        self, ipmi_ip: str, settings: IPMISettings
    ) -> IPMIConfigResult:
        """Configure generic IPMI when vendor is unknown."""
        result = IPMIConfigResult(
            success=False,
            vendor=IPMIVendor.UNKNOWN,
            settings_applied=[],
            errors=[],
            warnings=[],
        )

        try:
            # Basic connectivity and password test
            cmd = [
                "ipmitool",
                "-I",
                "lanplus",
                "-H",
                ipmi_ip,
                "-U",
                "ADMIN",
                "-P",
                settings.admin_password,
                "mc",
                "info",
            ]
            result_cmd = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result_cmd.returncode == 0:
                result.settings_applied.append("Basic IPMI connectivity verified")

                # Get firmware version if available
                for line in result_cmd.stdout.split("\n"):
                    if "Firmware Revision" in line:
                        result.firmware_version = line.split(":")[-1].strip()
                        break

                # Test power control
                cmd = [
                    "ipmitool",
                    "-I",
                    "lanplus",
                    "-H",
                    ipmi_ip,
                    "-U",
                    "ADMIN",
                    "-P",
                    settings.admin_password,
                    "power",
                    "status",
                ]
                result_cmd = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=10
                )
                if result_cmd.returncode == 0:
                    result.settings_applied.append("Power control verified")
                    result.success = True

                result.warnings.append(
                    "Unknown IPMI vendor - only basic configuration applied"
                )
            else:
                result.errors.append("Failed to connect to IPMI interface")

        except Exception as e:
            result.errors.append(f"Generic IPMI configuration error: {e}")

        return result

    def validate_ipmi_configuration(
        self, ipmi_ip: str, device_type: str, admin_password: str = None
    ) -> Dict[str, Any]:
        """
        Validate IPMI configuration against BMC boarding requirements

        Args:
            ipmi_ip: IPMI IP address
            device_type: BMC device type
            admin_password: Admin password

        Returns:
            Validation results dictionary
        ."""
        if admin_password is None:
            admin_password = self.config.get("ipmi_default_password", "ADMIN")

        validation: Dict[str, Any] = {
            "ipmi_accessible": False,
            "authentication_working": False,
            "power_control_working": False,
            "firmware_version": None,
            "vendor_detected": None,
            "requirements_met": [],
            "requirements_missing": [],
            "errors": [],
            "warnings": [],
        }

        try:
            # Test basic connectivity
            cmd = ["ping", "-c", "1", "-W", "2", ipmi_ip]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            validation["ipmi_accessible"] = result.returncode == 0

            if not validation["ipmi_accessible"]:
                validation["requirements_missing"].append(
                    "IPMI not accessible via ping"
                )
                return validation

            # Test IPMI authentication
            cmd = [
                "ipmitool",
                "-I",
                "lanplus",
                "-H",
                ipmi_ip,
                "-U",
                "ADMIN",
                "-P",
                admin_password,
                "mc",
                "info",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            validation["authentication_working"] = result.returncode == 0

            if validation["authentication_working"]:
                validation["requirements_met"].append("IPMI authentication working")

                # Extract firmware version
                for line in result.stdout.split("\n"):
                    if "Firmware Revision" in line:
                        validation["firmware_version"] = line.split(":")[-1].strip()
                        break

                # Detect vendor
                vendor = self.detect_ipmi_vendor(ipmi_ip, "ADMIN", admin_password)
                validation["vendor_detected"] = vendor.value

                # Test power control
                cmd = [
                    "ipmitool",
                    "-I",
                    "lanplus",
                    "-H",
                    ipmi_ip,
                    "-U",
                    "ADMIN",
                    "-P",
                    admin_password,
                    "power",
                    "status",
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                validation["power_control_working"] = result.returncode == 0

                if validation["power_control_working"]:
                    validation["requirements_met"].append("Power control working")
                else:
                    validation["requirements_missing"].append(
                        "Power control not working"
                    )
            else:
                validation["requirements_missing"].append("IPMI authentication failed")

        except Exception as e:
            validation["warnings"].append(f"Validation error: {e}")

        return validation
