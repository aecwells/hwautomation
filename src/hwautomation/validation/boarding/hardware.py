"""
Hardware validation handler.

Validates hardware information discovery and basic hardware functionality.
"""

from typing import List

from ...logging import get_logger
from ...utils.network import SSHClient
from .base import (
    ValidationCategory,
    ValidationConfig,
    ValidationHandler,
    ValidationResult,
    ValidationStatus,
)

logger = get_logger(__name__)


class HardwareValidationHandler(ValidationHandler):
    """Handles hardware validation checks."""

    def get_category(self) -> ValidationCategory:
        """Get the validation category this handler manages."""
        return ValidationCategory.HARDWARE

    def get_required_prerequisites(self) -> List[ValidationCategory]:
        """Get list of validation categories that must pass before this one."""
        return [ValidationCategory.CONNECTIVITY]

    def validate(self, config: ValidationConfig) -> List[ValidationResult]:
        """Execute hardware validation checks."""
        logger.info(f"Starting hardware validation for {config.device_id}")
        results = []

        try:
            ssh_client = SSHClient()
            success = ssh_client.connect(
                hostname=config.server_ip,
                username=config.ssh_username,
                timeout=config.ssh_timeout,
            )

            if not success:
                results.append(
                    ValidationResult(
                        check_name="hardware_ssh_connection",
                        status=ValidationStatus.FAIL,
                        message="Cannot establish SSH connection for hardware validation",
                        category=self.get_category(),
                        remediation="Ensure SSH connectivity is working",
                    )
                )
                return results

            # Validate CPU information
            results.extend(self._validate_cpu_info(ssh_client, config))

            # Validate memory information
            results.extend(self._validate_memory_info(ssh_client, config))

            # Validate storage information
            results.extend(self._validate_storage_info(ssh_client, config))

            # Validate network interfaces
            results.extend(self._validate_network_interfaces(ssh_client, config))

            ssh_client.disconnect()

        except Exception as e:
            results.append(
                ValidationResult(
                    check_name="hardware_discovery",
                    status=ValidationStatus.FAIL,
                    message=f"Hardware information discovery failed: {e}",
                    category=self.get_category(),
                    remediation="Ensure SSH access is working and system is fully booted",
                )
            )

        logger.info(
            f"Hardware validation completed for {config.device_id}: {len(results)} checks"
        )
        return results

    def _validate_cpu_info(
        self, ssh_client: SSHClient, config: ValidationConfig
    ) -> List[ValidationResult]:
        """Validate CPU information detection."""
        results = []

        try:
            result = ssh_client.exec_command("lscpu | grep 'Model name'")
            if result.exit_code == 0 and result.stdout.strip():
                cpu_model = result.stdout.strip()
                results.append(
                    ValidationResult(
                        check_name="cpu_detection",
                        status=ValidationStatus.PASS,
                        message="CPU information detected successfully",
                        category=self.get_category(),
                        details={"cpu_model": cpu_model},
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="cpu_detection",
                        status=ValidationStatus.FAIL,
                        message="Failed to detect CPU information",
                        category=self.get_category(),
                    )
                )
        except Exception as e:
            results.append(
                ValidationResult(
                    check_name="cpu_detection",
                    status=ValidationStatus.FAIL,
                    message=f"CPU detection error: {e}",
                    category=self.get_category(),
                )
            )

        return results

    def _validate_memory_info(
        self, ssh_client: SSHClient, config: ValidationConfig
    ) -> List[ValidationResult]:
        """Validate memory information detection."""
        results = []

        try:
            result = ssh_client.exec_command("free -h | grep 'Mem:'")
            if result.exit_code == 0 and result.stdout.strip():
                memory_info = result.stdout.strip()
                results.append(
                    ValidationResult(
                        check_name="memory_detection",
                        status=ValidationStatus.PASS,
                        message="Memory information detected successfully",
                        category=self.get_category(),
                        details={"memory_info": memory_info},
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="memory_detection",
                        status=ValidationStatus.FAIL,
                        message="Failed to detect memory information",
                        category=self.get_category(),
                    )
                )
        except Exception as e:
            results.append(
                ValidationResult(
                    check_name="memory_detection",
                    status=ValidationStatus.FAIL,
                    message=f"Memory detection error: {e}",
                    category=self.get_category(),
                )
            )

        return results

    def _validate_storage_info(
        self, ssh_client: SSHClient, config: ValidationConfig
    ) -> List[ValidationResult]:
        """Validate storage information detection."""
        results = []

        try:
            result = ssh_client.exec_command(
                "lsblk -d -o NAME,SIZE,MODEL | grep -v loop"
            )
            if result.exit_code == 0 and result.stdout.strip():
                storage_info = result.stdout.strip()
                results.append(
                    ValidationResult(
                        check_name="storage_detection",
                        status=ValidationStatus.PASS,
                        message="Storage information detected successfully",
                        category=self.get_category(),
                        details={"storage_info": storage_info},
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="storage_detection",
                        status=ValidationStatus.WARNING,
                        message="Storage information may be incomplete",
                        category=self.get_category(),
                    )
                )
        except Exception as e:
            results.append(
                ValidationResult(
                    check_name="storage_detection",
                    status=ValidationStatus.WARNING,
                    message=f"Storage detection error: {e}",
                    category=self.get_category(),
                )
            )

        return results

    def _validate_network_interfaces(
        self, ssh_client: SSHClient, config: ValidationConfig
    ) -> List[ValidationResult]:
        """Validate network interface detection."""
        results = []

        try:
            result = ssh_client.exec_command(
                "ip link show | grep -E '^[0-9]+:' | grep -v lo"
            )
            if result.exit_code == 0 and result.stdout.strip():
                interfaces = result.stdout.strip().split("\n")
                nic_count = len(interfaces)

                results.append(
                    ValidationResult(
                        check_name="network_interfaces",
                        status=ValidationStatus.PASS,
                        message=f"Detected {nic_count} network interfaces",
                        category=self.get_category(),
                        details={
                            "interface_count": nic_count,
                            "interfaces": result.stdout.strip(),
                        },
                    )
                )

                # Check for minimum interface count
                if nic_count >= 2:
                    results.append(
                        ValidationResult(
                            check_name="network_interface_count",
                            status=ValidationStatus.PASS,
                            message=f"Found {nic_count} network interfaces (minimum 2 required)",
                            category=self.get_category(),
                        )
                    )
                else:
                    results.append(
                        ValidationResult(
                            check_name="network_interface_count",
                            status=ValidationStatus.WARNING,
                            message=f"Only {nic_count} network interface(s) found",
                            category=self.get_category(),
                        )
                    )
            else:
                results.append(
                    ValidationResult(
                        check_name="network_interfaces",
                        status=ValidationStatus.FAIL,
                        message="Failed to detect network interfaces",
                        category=self.get_category(),
                    )
                )
        except Exception as e:
            results.append(
                ValidationResult(
                    check_name="network_interfaces",
                    status=ValidationStatus.FAIL,
                    message=f"Network interface detection error: {e}",
                    category=self.get_category(),
                )
            )

        return results
