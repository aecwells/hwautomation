"""
BMC Boarding Validation Service

Implements validation steps from the BMC boarding process document.
Ensures all requirements are met before considering a device properly configured.
."""

import logging
import re
import subprocess
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..utils.network import SSHClient

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation status levels."""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


@dataclass
class ValidationResult:
    """Individual validation result."""

    check_name: str
    status: ValidationStatus
    message: str
    details: Optional[Dict] = None
    remediation: Optional[str] = None


@dataclass
class BoardingValidation:
    """Complete boarding validation results."""

    device_id: str
    device_type: str
    overall_status: ValidationStatus
    validations: List[ValidationResult] = field(default_factory=list)
    summary: Dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        """Calculate summary after initialization."""
        self.update_summary()

    def update_summary(self):
        """Update validation summary counts."""
        self.summary = {
            "total": len(self.validations),
            "passed": len(
                [v for v in self.validations if v.status == ValidationStatus.PASS]
            ),
            "failed": len(
                [v for v in self.validations if v.status == ValidationStatus.FAIL]
            ),
            "warnings": len(
                [v for v in self.validations if v.status == ValidationStatus.WARNING]
            ),
            "skipped": len(
                [v for v in self.validations if v.status == ValidationStatus.SKIP]
            ),
        }

        # Determine overall status
        if self.summary["failed"] > 0:
            self.overall_status = ValidationStatus.FAIL
        elif self.summary["warnings"] > 0:
            self.overall_status = ValidationStatus.WARNING
        else:
            self.overall_status = ValidationStatus.PASS


class BMCBoardingValidator:
    """Validates BMC boarding according to the boarding process document."""

    def __init__(self, config: Dict = None):
        """
        Initialize BMC boarding validator

        Args:
            config: Configuration dictionary
        ."""
        self.config = config or {}
        self.required_bios_settings = self._load_bios_requirements()
        self.required_ipmi_settings = self._load_ipmi_requirements()

    def _load_bios_requirements(self) -> Dict[str, Dict]:
        """Load BIOS requirements from boarding document."""
        return {
            "rocketlake": {
                "security": {
                    "administrator_password": "set",
                    "secure_boot": "disabled",
                    "csm_support": "disabled",
                },
                "boot": {
                    "boot_mode": "uefi",
                    "boot_order": [
                        "UEFI USB CD/DVD",
                        "UEFI USB Key",
                        "UEFI USB Hard Disk",
                        "UEFI Hard Disk",
                        "UEFI Network",
                    ],
                },
                "advanced": {
                    "sgx_settings": "enabled",
                    "internal_graphics": "enabled",
                    "sata_controller": "disabled",
                    "ssata_controller": "disabled",
                },
            },
            "coffeelake": {
                "security": {
                    "administrator_password": "set",
                    "secure_boot": "disabled",
                    "csm_support": "disabled",
                },
                "boot": {
                    "boot_mode": "uefi",
                    "boot_order": [
                        "UEFI USB CD/DVD",
                        "UEFI USB Key",
                        "UEFI USB Hard Disk",
                        "UEFI Hard Disk",
                        "UEFI Network",
                    ],
                },
                "advanced": {
                    "internal_graphics": "enabled",
                    "sgx": "enabled",
                    "sata_controller": "disabled",
                    "ssata_controller": "disabled",
                },
            },
            "cascadelake": {
                "security": {
                    "administrator_password": "set",
                    "secure_boot": "disabled",
                    "csm_support": "disabled",
                },
                "boot": {
                    "boot_mode": "uefi",
                    "boot_order": [
                        "UEFI USB CD/DVD",
                        "UEFI USB Key",
                        "UEFI USB Hard Disk",
                        "UEFI Hard Disk",
                        "UEFI Network",
                    ],
                },
                "advanced": {
                    "hardware_p_states": "native_mode",
                    "sata_controller": "disabled",
                    "ssata_controller": "disabled",
                },
            },
            "icelake_spr": {
                "security": {
                    "administrator_password": "set",
                    "secure_boot": "disabled",
                    "csm_support": "disabled",
                },
                "boot": {
                    "boot_mode": "uefi",
                    "boot_order": [
                        "UEFI USB Key",
                        "UEFI USB CD/DVD",
                        "UEFI USB Hard Disk",
                        "UEFI Hard Disk",
                        "UEFI Network",
                    ],
                },
                "advanced": {
                    "speedstep_p_states": "enabled",
                    "hardware_p_states": "native_mode",
                    "sata_controller": "disabled",
                    "ssata_controller": "disabled",
                    "tme": "enabled",  # For SGX builds
                    "sgx": "enabled",  # For SGX builds
                },
            },
            "hp_ilo": {
                "boot": {
                    "boot_order_policy": "retry_once",
                    "pre_boot_network": "ipv4",
                    "network_boot_retry": "2",
                    "http_support": "disabled",
                    "iscsi_initiator": "disabled",
                },
                "security": {
                    "secure_boot": "disabled",
                    "platform_certificate": "disabled",
                    "ilo_accounts": "disabled",
                    "intelligent_provisioning": "disabled",
                    "tpm_visibility": "hidden",
                },
            },
        }

    def _load_ipmi_requirements(self) -> Dict[str, Dict]:
        """Load IPMI requirements from boarding document."""
        return {
            "supermicro": {
                "oob_license": "activated",
                "admin_password": "set",
                "kcs_control": "user",
                "host_interface": "off",
            },
            "hp_ilo": {
                "ipmi_over_lan": "enabled",
                "require_host_auth": "enabled",
                "require_login_rbsu": "enabled",
                "admin_user": "created",
            },
        }

    def validate_complete_boarding(
        self, device_id: str, device_type: str, server_ip: str, ipmi_ip: str
    ) -> BoardingValidation:
        """
        Perform complete boarding validation for a device

        Args:
            device_id: Device identifier
            device_type: BMC device type
            server_ip: Server IP address
            ipmi_ip: IPMI IP address

        Returns:
            Complete validation results
        ."""
        validation = BoardingValidation(
            device_id=device_id,
            device_type=device_type,
            overall_status=ValidationStatus.PASS,
        )

        logger.info(
            f"Starting complete boarding validation for {device_id} ({device_type})"
        )

        # 1. Validate basic connectivity
        validation.validations.extend(
            self._validate_connectivity(device_id, server_ip, ipmi_ip)
        )

        # 2. Validate hardware information
        validation.validations.extend(
            self._validate_hardware_info(device_id, server_ip)
        )

        # 3. Validate IPMI configuration
        validation.validations.extend(
            self._validate_ipmi_configuration(device_id, ipmi_ip, device_type)
        )

        # 4. Validate BIOS configuration (if accessible)
        validation.validations.extend(
            self._validate_bios_configuration(device_id, server_ip, device_type)
        )

        # 5. Validate network configuration
        validation.validations.extend(
            self._validate_network_configuration(device_id, server_ip)
        )

        # 6. Validate device page requirements
        validation.validations.extend(
            self._validate_device_page_requirements(device_id, device_type)
        )

        # Update summary and overall status
        validation.update_summary()

        logger.info(
            f"Boarding validation complete for {device_id}: {validation.overall_status.value} "
            f"({validation.summary['passed']}/{validation.summary['total']} passed)"
        )

        return validation

    def _validate_connectivity(
        self, device_id: str, server_ip: str, ipmi_ip: str
    ) -> List[ValidationResult]:
        """Validate basic connectivity to server and IPMI."""
        results = []

        # Test server IP connectivity
        try:
            cmd = ["ping", "-c", "3", "-W", "2", server_ip]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                results.append(
                    ValidationResult(
                        check_name="server_connectivity",
                        status=ValidationStatus.PASS,
                        message=f"Server {server_ip} is reachable",
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="server_connectivity",
                        status=ValidationStatus.FAIL,
                        message=f"Server {server_ip} is not reachable",
                        remediation="Check network configuration and server power status",
                    )
                )
        except Exception as e:
            results.append(
                ValidationResult(
                    check_name="server_connectivity",
                    status=ValidationStatus.FAIL,
                    message=f"Error testing server connectivity: {e}",
                )
            )

        # Test IPMI connectivity
        try:
            cmd = ["ping", "-c", "3", "-W", "2", ipmi_ip]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                results.append(
                    ValidationResult(
                        check_name="ipmi_connectivity",
                        status=ValidationStatus.PASS,
                        message=f"IPMI {ipmi_ip} is reachable",
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="ipmi_connectivity",
                        status=ValidationStatus.FAIL,
                        message=f"IPMI {ipmi_ip} is not reachable",
                        remediation="Check IPMI network configuration",
                    )
                )
        except Exception as e:
            results.append(
                ValidationResult(
                    check_name="ipmi_connectivity",
                    status=ValidationStatus.FAIL,
                    message=f"Error testing IPMI connectivity: {e}",
                )
            )

        # Test SSH connectivity to server
        try:
            ssh_client = SSHClient(server_ip, username="root", timeout=10)
            ssh_client.connect()

            results.append(
                ValidationResult(
                    check_name="ssh_connectivity",
                    status=ValidationStatus.PASS,
                    message=f"SSH connection to {server_ip} successful",
                )
            )
            ssh_client.close()

        except Exception as e:
            results.append(
                ValidationResult(
                    check_name="ssh_connectivity",
                    status=ValidationStatus.FAIL,
                    message=f"SSH connection to {server_ip} failed: {e}",
                    remediation="Check SSH service status and authentication",
                )
            )

        return results

    def _validate_hardware_info(
        self, device_id: str, server_ip: str
    ) -> List[ValidationResult]:
        """Validate hardware information discovery."""
        results = []

        try:
            ssh_client = SSHClient(server_ip, username="root", timeout=30)
            ssh_client.connect()

            # Check CPU information
            stdout, stderr, exit_code = ssh_client.exec_command(
                "lscpu | grep 'Model name'"
            )
            if exit_code == 0 and stdout and "Intel" in stdout:
                results.append(
                    ValidationResult(
                        check_name="cpu_detection",
                        status=ValidationStatus.PASS,
                        message="CPU information detected successfully",
                        details={"cpu_info": stdout.strip()},
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="cpu_detection",
                        status=ValidationStatus.WARNING,
                        message="CPU information may not be complete",
                        details={"cpu_info": stdout if stdout else ""},
                    )
                )

            # Check memory information
            stdout, stderr, exit_code = ssh_client.exec_command("free -h | grep 'Mem:'")
            if exit_code == 0 and stdout:
                results.append(
                    ValidationResult(
                        check_name="memory_detection",
                        status=ValidationStatus.PASS,
                        message="Memory information detected successfully",
                        details={"memory_info": stdout.strip()},
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="memory_detection",
                        status=ValidationStatus.FAIL,
                        message="Failed to detect memory information",
                    )
                )

            # Check disk information
            stdout, stderr, exit_code = ssh_client.exec_command(
                "lsblk -d -o NAME,SIZE,MODEL | grep -v loop"
            )
            if exit_code == 0 and stdout:
                results.append(
                    ValidationResult(
                        check_name="storage_detection",
                        status=ValidationStatus.PASS,
                        message="Storage information detected successfully",
                        details={"storage_info": stdout.strip()},
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="storage_detection",
                        status=ValidationStatus.WARNING,
                        message="Storage information may be incomplete",
                    )
                )

            # Check network interfaces
            stdout, stderr, exit_code = ssh_client.exec_command(
                "ip link show | grep -E '^[0-9]+:' | grep -v lo"
            )
            if exit_code == 0 and stdout:
                nic_count = len(stdout.strip().split("\n"))
                results.append(
                    ValidationResult(
                        check_name="network_interfaces",
                        status=ValidationStatus.PASS,
                        message=f"Detected {nic_count} network interfaces",
                        details={"interfaces": stdout.strip()},
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="network_interfaces",
                        status=ValidationStatus.FAIL,
                        message="Failed to detect network interfaces",
                    )
                )

            ssh_client.close()

        except Exception as e:
            results.append(
                ValidationResult(
                    check_name="hardware_discovery",
                    status=ValidationStatus.FAIL,
                    message=f"Hardware information discovery failed: {e}",
                    remediation="Ensure SSH access is working and system is fully booted",
                )
            )

        return results

    def _validate_ipmi_configuration(
        self, device_id: str, ipmi_ip: str, device_type: str
    ) -> List[ValidationResult]:
        """Validate IPMI configuration according to boarding requirements."""
        results = []

        try:
            # Test basic IPMI functionality
            admin_password = self.config.get("ipmi_default_password", "ADMIN")
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
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

            if result.returncode == 0:
                results.append(
                    ValidationResult(
                        check_name="ipmi_authentication",
                        status=ValidationStatus.PASS,
                        message="IPMI authentication successful",
                    )
                )

                # Extract firmware version
                firmware_version = None
                for line in result.stdout.split("\n"):
                    if "Firmware Revision" in line:
                        firmware_version = line.split(":")[-1].strip()
                        break

                if firmware_version:
                    results.append(
                        ValidationResult(
                            check_name="ipmi_firmware",
                            status=ValidationStatus.PASS,
                            message=f"IPMI firmware version: {firmware_version}",
                            details={"firmware_version": firmware_version},
                        )
                    )

            else:
                results.append(
                    ValidationResult(
                        check_name="ipmi_authentication",
                        status=ValidationStatus.FAIL,
                        message="IPMI authentication failed",
                        remediation="Check IPMI credentials and network configuration",
                    )
                )
                return results  # Can't continue without authentication

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

            if result.returncode == 0:
                power_status = result.stdout.strip()
                results.append(
                    ValidationResult(
                        check_name="ipmi_power_control",
                        status=ValidationStatus.PASS,
                        message=f"IPMI power control working - Status: {power_status}",
                        details={"power_status": power_status},
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="ipmi_power_control",
                        status=ValidationStatus.FAIL,
                        message="IPMI power control not working",
                        remediation="Check IPMI configuration and permissions",
                    )
                )

            # Test sensor reading
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
                "sensor",
                "list",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

            if result.returncode == 0:
                sensor_count = len(
                    [
                        line
                        for line in result.stdout.split("\n")
                        if line.strip() and "|" in line
                    ]
                )
                results.append(
                    ValidationResult(
                        check_name="ipmi_sensors",
                        status=ValidationStatus.PASS,
                        message=f"IPMI sensors accessible - {sensor_count} sensors found",
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="ipmi_sensors",
                        status=ValidationStatus.WARNING,
                        message="IPMI sensor access limited - may indicate OOB license issue",
                    )
                )

        except subprocess.TimeoutExpired:
            results.append(
                ValidationResult(
                    check_name="ipmi_timeout",
                    status=ValidationStatus.FAIL,
                    message="IPMI commands timed out",
                    remediation="Check IPMI network connectivity and performance",
                )
            )
        except Exception as e:
            results.append(
                ValidationResult(
                    check_name="ipmi_validation",
                    status=ValidationStatus.FAIL,
                    message=f"IPMI validation error: {e}",
                )
            )

        return results

    def _validate_bios_configuration(
        self, device_id: str, server_ip: str, device_type: str
    ) -> List[ValidationResult]:
        """Validate BIOS configuration (basic checks via OS)."""
        results = []

        try:
            ssh_client = SSHClient(server_ip, username="root", timeout=30)
            ssh_client.connect()

            # Check boot mode (UEFI vs Legacy)
            stdout, stderr, exit_code = ssh_client.exec_command(
                "[ -d /sys/firmware/efi ] && echo 'UEFI' || echo 'Legacy'"
            )
            if exit_code == 0 and stdout and "UEFI" in stdout:
                results.append(
                    ValidationResult(
                        check_name="boot_mode",
                        status=ValidationStatus.PASS,
                        message="System is booted in UEFI mode",
                    )
                )
            elif exit_code == 0 and stdout and "Legacy" in stdout:
                results.append(
                    ValidationResult(
                        check_name="boot_mode",
                        status=ValidationStatus.WARNING,
                        message="System is booted in Legacy mode - UEFI may be required",
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="boot_mode",
                        status=ValidationStatus.FAIL,
                        message="Could not determine boot mode",
                    )
                )

            # Check for Secure Boot status
            stdout, stderr, exit_code = ssh_client.exec_command(
                "mokutil --sb-state 2>/dev/null || echo 'Not available'"
            )
            if exit_code == 0 and stdout and "disabled" in stdout.lower():
                results.append(
                    ValidationResult(
                        check_name="secure_boot",
                        status=ValidationStatus.PASS,
                        message="Secure Boot is disabled as required",
                    )
                )
            elif exit_code == 0 and stdout and "enabled" in stdout.lower():
                results.append(
                    ValidationResult(
                        check_name="secure_boot",
                        status=ValidationStatus.WARNING,
                        message="Secure Boot is enabled - may need to be disabled",
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="secure_boot",
                        status=ValidationStatus.SKIP,
                        message="Secure Boot status not available",
                    )
                )

            # Check CPU features (for specific device types)
            if "sgx" in device_type.lower() or any(
                x in device_type for x in ["s5", "icx", "spr"]
            ):
                stdout, stderr, exit_code = ssh_client.exec_command(
                    "grep -i sgx /proc/cpuinfo | head -1"
                )
                if exit_code == 0 and stdout:
                    results.append(
                        ValidationResult(
                            check_name="sgx_support",
                            status=ValidationStatus.PASS,
                            message="SGX support detected in CPU",
                        )
                    )
                else:
                    results.append(
                        ValidationResult(
                            check_name="sgx_support",
                            status=ValidationStatus.WARNING,
                            message="SGX support not detected - may need BIOS configuration",
                        )
                    )

            ssh_client.close()

        except Exception as e:
            results.append(
                ValidationResult(
                    check_name="bios_validation",
                    status=ValidationStatus.WARNING,
                    message=f"BIOS validation limited due to error: {e}",
                )
            )

        return results

    def _validate_network_configuration(
        self, device_id: str, server_ip: str
    ) -> List[ValidationResult]:
        """Validate network configuration."""
        results = []

        try:
            ssh_client = SSHClient(server_ip, username="root", timeout=30)
            ssh_client.connect()

            # Check network interface count
            stdout, stderr, exit_code = ssh_client.exec_command(
                "ip link show | grep -E '^[0-9]+:' | grep -v lo | wc -l"
            )
            if exit_code == 0 and stdout:
                iface_count = int(stdout.strip())
                if iface_count >= 2:
                    results.append(
                        ValidationResult(
                            check_name="network_interfaces_count",
                            status=ValidationStatus.PASS,
                            message=f"Found {iface_count} network interfaces (minimum 2 required)",
                        )
                    )
                else:
                    results.append(
                        ValidationResult(
                            check_name="network_interfaces_count",
                            status=ValidationStatus.WARNING,
                            message=f"Only {iface_count} network interface(s) found",
                        )
                    )

            # Check for active network interfaces
            stdout, stderr, exit_code = ssh_client.exec_command(
                "ip link show up | grep -E '^[0-9]+:' | grep -v lo | wc -l"
            )
            if exit_code == 0 and stdout:
                active_count = int(stdout.strip())
                results.append(
                    ValidationResult(
                        check_name="active_interfaces",
                        status=ValidationStatus.PASS,
                        message=f"Found {active_count} active network interfaces",
                    )
                )

            # Check DNS resolution
            stdout, stderr, exit_code = ssh_client.exec_command(
                "nslookup google.com >/dev/null 2>&1 && echo 'OK' || echo 'FAIL'"
            )
            if exit_code == 0 and stdout and "OK" in stdout:
                results.append(
                    ValidationResult(
                        check_name="dns_resolution",
                        status=ValidationStatus.PASS,
                        message="DNS resolution working",
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="dns_resolution",
                        status=ValidationStatus.WARNING,
                        message="DNS resolution may not be working",
                    )
                )

            ssh_client.close()

        except Exception as e:
            results.append(
                ValidationResult(
                    check_name="network_validation",
                    status=ValidationStatus.WARNING,
                    message=f"Network validation error: {e}",
                )
            )

        return results

    def _validate_device_page_requirements(
        self, device_id: str, device_type: str
    ) -> List[ValidationResult]:
        """Validate device page requirements from boarding document."""
        results = []

        # This would typically validate against your device management system
        # For now, we'll do basic validation checks

        results.append(
            ValidationResult(
                check_name="device_type_set",
                status=ValidationStatus.PASS,
                message=f"Device type set to: {device_type}",
            )
        )

        # Check if device type is BMC server type
        if any(
            prefix in device_type
            for prefix in [
                "d1.",
                "d2.",
                "d3.",
                "s1.",
                "s2.",
                "s3.",
                "s4.",
                "s5.",
                "hp.",
            ]
        ):
            results.append(
                ValidationResult(
                    check_name="bmc_server_type",
                    status=ValidationStatus.PASS,
                    message="Device type is a valid BMC server type",
                )
            )
        else:
            results.append(
                ValidationResult(
                    check_name="bmc_server_type",
                    status=ValidationStatus.WARNING,
                    message="Device type may not be a standard BMC server type",
                )
            )

        # Validate required fields would be present
        required_fields = [
            "Switch port eth0 – AR1",
            "Switch port eth1 – AR2",
            "Switch port eth2 – IPMI",
            "CPU, Memory type, Memory Amount",
            "HDD1, HDD2, NIC Speed",
            "MAC Address eth0, MAC Address eth1",
            "BMC Server Type, IPMI Address",
        ]

        for field in required_fields:
            results.append(
                ValidationResult(
                    check_name=f"required_field_{field.lower().replace(' ', '_').replace('–', '').replace(',', '')}",
                    status=ValidationStatus.SKIP,
                    message=f"Field '{field}' should be configured in device page",
                )
            )

        return results
