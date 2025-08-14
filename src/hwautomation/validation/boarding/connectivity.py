"""
Connectivity validation handler.

Validates basic network connectivity to server and IPMI interfaces.
"""

import subprocess
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


class ConnectivityValidationHandler(ValidationHandler):
    """Handles connectivity validation checks."""

    def get_category(self) -> ValidationCategory:
        """Get the validation category this handler manages."""
        return ValidationCategory.CONNECTIVITY

    def get_required_prerequisites(self) -> List[ValidationCategory]:
        """Get list of validation categories that must pass before this one."""
        return []  # Connectivity is the first check

    def validate(self, config: ValidationConfig) -> List[ValidationResult]:
        """Execute connectivity validation checks."""
        logger.info(f"Starting connectivity validation for {config.device_id}")
        results = []

        # Test server IP connectivity
        results.extend(self._test_server_connectivity(config))

        # Test IPMI connectivity
        results.extend(self._test_ipmi_connectivity(config))

        # Test SSH connectivity
        results.extend(self._test_ssh_connectivity(config))

        logger.info(
            f"Connectivity validation completed for {config.device_id}: {len(results)} checks"
        )
        return results

    def _test_server_connectivity(
        self, config: ValidationConfig
    ) -> List[ValidationResult]:
        """Test basic network connectivity to server."""
        results = []

        try:
            cmd = ["ping", "-c", "3", "-W", "2", config.server_ip]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                results.append(
                    ValidationResult(
                        check_name="server_ping",
                        status=ValidationStatus.PASS,
                        message=f"Server {config.server_ip} is reachable",
                        category=self.get_category(),
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="server_ping",
                        status=ValidationStatus.FAIL,
                        message=f"Server {config.server_ip} is not reachable",
                        category=self.get_category(),
                        remediation="Check network configuration and server power status",
                    )
                )
        except Exception as e:
            results.append(
                ValidationResult(
                    check_name="server_ping",
                    status=ValidationStatus.FAIL,
                    message=f"Error testing server connectivity: {e}",
                    category=self.get_category(),
                )
            )

        return results

    def _test_ipmi_connectivity(
        self, config: ValidationConfig
    ) -> List[ValidationResult]:
        """Test basic network connectivity to IPMI interface."""
        results = []

        try:
            cmd = ["ping", "-c", "3", "-W", "2", config.ipmi_ip]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                results.append(
                    ValidationResult(
                        check_name="ipmi_ping",
                        status=ValidationStatus.PASS,
                        message=f"IPMI {config.ipmi_ip} is reachable",
                        category=self.get_category(),
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="ipmi_ping",
                        status=ValidationStatus.FAIL,
                        message=f"IPMI {config.ipmi_ip} is not reachable",
                        category=self.get_category(),
                        remediation="Check IPMI network configuration",
                    )
                )
        except Exception as e:
            results.append(
                ValidationResult(
                    check_name="ipmi_ping",
                    status=ValidationStatus.FAIL,
                    message=f"Error testing IPMI connectivity: {e}",
                    category=self.get_category(),
                )
            )

        return results

    def _test_ssh_connectivity(
        self, config: ValidationConfig
    ) -> List[ValidationResult]:
        """Test SSH connectivity to server."""
        results = []

        try:
            ssh_client = SSHClient()
            success = ssh_client.connect(
                hostname=config.server_ip,
                username=config.ssh_username,
                timeout=config.ssh_timeout,
            )

            if success:
                # Test a simple command
                cmd_result = ssh_client.exec_command("echo 'SSH test successful'")
                ssh_client.disconnect()

                if cmd_result.exit_code == 0:
                    results.append(
                        ValidationResult(
                            check_name="ssh_connectivity",
                            status=ValidationStatus.PASS,
                            message=f"SSH connection to {config.server_ip} successful",
                            category=self.get_category(),
                        )
                    )
                else:
                    results.append(
                        ValidationResult(
                            check_name="ssh_connectivity",
                            status=ValidationStatus.FAIL,
                            message=f"SSH command execution failed on {config.server_ip}",
                            category=self.get_category(),
                            remediation="Check SSH service configuration",
                        )
                    )
            else:
                results.append(
                    ValidationResult(
                        check_name="ssh_connectivity",
                        status=ValidationStatus.FAIL,
                        message=f"SSH connection to {config.server_ip} failed",
                        category=self.get_category(),
                        remediation="Check SSH service status and authentication",
                    )
                )

        except Exception as e:
            results.append(
                ValidationResult(
                    check_name="ssh_connectivity",
                    status=ValidationStatus.FAIL,
                    message=f"SSH connection to {config.server_ip} failed: {e}",
                    category=self.get_category(),
                    remediation="Check SSH service status and authentication",
                )
            )

        return results
