"""
IPMI validation handler.

Validates IPMI configuration and functionality.
"""

import subprocess
from typing import List

from ...logging import get_logger
from .base import (
    ValidationCategory,
    ValidationConfig,
    ValidationHandler,
    ValidationResult,
    ValidationStatus,
)

logger = get_logger(__name__)


class IpmiValidationHandler(ValidationHandler):
    """Handles IPMI validation checks."""

    def get_category(self) -> ValidationCategory:
        """Get the validation category this handler manages."""
        return ValidationCategory.IPMI

    def get_required_prerequisites(self) -> List[ValidationCategory]:
        """Get list of validation categories that must pass before this one."""
        return [ValidationCategory.CONNECTIVITY]

    def validate(self, config: ValidationConfig) -> List[ValidationResult]:
        """Execute IPMI validation checks."""
        logger.info(f"Starting IPMI validation for {config.device_id}")
        results = []

        # Test basic IPMI authentication
        auth_result = self._test_ipmi_authentication(config)
        results.extend(auth_result)

        # Only continue with other tests if authentication works
        auth_passed = any(
            r.status == ValidationStatus.PASS and r.check_name == "ipmi_authentication"
            for r in auth_result
        )

        if auth_passed:
            # Test IPMI functionality
            results.extend(self._test_ipmi_functionality(config))
            results.extend(self._test_ipmi_sensors(config))
            results.extend(self._test_power_control(config))
        else:
            results.append(
                ValidationResult(
                    check_name="ipmi_extended_tests",
                    status=ValidationStatus.SKIP,
                    message="Skipping extended IPMI tests due to authentication failure",
                    category=self.get_category(),
                )
            )

        logger.info(
            f"IPMI validation completed for {config.device_id}: {len(results)} checks"
        )
        return results

    def _test_ipmi_authentication(
        self, config: ValidationConfig
    ) -> List[ValidationResult]:
        """Test basic IPMI authentication."""
        results = []

        try:
            cmd = [
                "ipmitool",
                "-I",
                "lanplus",
                "-H",
                config.ipmi_ip,
                "-U",
                config.ipmi_username,
                "-P",
                config.ipmi_password,
                "mc",
                "info",
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=config.ipmi_timeout
            )

            if result.returncode == 0:
                results.append(
                    ValidationResult(
                        check_name="ipmi_authentication",
                        status=ValidationStatus.PASS,
                        message="IPMI authentication successful",
                        category=self.get_category(),
                    )
                )

                # Extract firmware version
                firmware_version = self._extract_firmware_version(result.stdout)
                if firmware_version:
                    results.append(
                        ValidationResult(
                            check_name="ipmi_firmware",
                            status=ValidationStatus.PASS,
                            message=f"IPMI firmware version: {firmware_version}",
                            category=self.get_category(),
                            details={"firmware_version": firmware_version},
                        )
                    )
            else:
                results.append(
                    ValidationResult(
                        check_name="ipmi_authentication",
                        status=ValidationStatus.FAIL,
                        message="IPMI authentication failed",
                        category=self.get_category(),
                        remediation="Check IPMI credentials and network configuration",
                    )
                )

        except subprocess.TimeoutExpired:
            results.append(
                ValidationResult(
                    check_name="ipmi_authentication",
                    status=ValidationStatus.FAIL,
                    message="IPMI authentication timed out",
                    category=self.get_category(),
                    remediation="Check IPMI network connectivity and performance",
                )
            )
        except Exception as e:
            results.append(
                ValidationResult(
                    check_name="ipmi_authentication",
                    status=ValidationStatus.FAIL,
                    message=f"IPMI authentication error: {e}",
                    category=self.get_category(),
                )
            )

        return results

    def _test_ipmi_functionality(
        self, config: ValidationConfig
    ) -> List[ValidationResult]:
        """Test basic IPMI functionality."""
        results = []

        try:
            # Test BMC info
            cmd = [
                "ipmitool",
                "-I",
                "lanplus",
                "-H",
                config.ipmi_ip,
                "-U",
                config.ipmi_username,
                "-P",
                config.ipmi_password,
                "bmc",
                "info",
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=config.ipmi_timeout
            )

            if result.returncode == 0:
                results.append(
                    ValidationResult(
                        check_name="ipmi_bmc_info",
                        status=ValidationStatus.PASS,
                        message="BMC information accessible",
                        category=self.get_category(),
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="ipmi_bmc_info",
                        status=ValidationStatus.WARNING,
                        message="BMC information access limited",
                        category=self.get_category(),
                    )
                )

        except Exception as e:
            results.append(
                ValidationResult(
                    check_name="ipmi_bmc_info",
                    status=ValidationStatus.FAIL,
                    message=f"BMC info test error: {e}",
                    category=self.get_category(),
                )
            )

        return results

    def _test_ipmi_sensors(self, config: ValidationConfig) -> List[ValidationResult]:
        """Test IPMI sensor access."""
        results = []

        try:
            cmd = [
                "ipmitool",
                "-I",
                "lanplus",
                "-H",
                config.ipmi_ip,
                "-U",
                config.ipmi_username,
                "-P",
                config.ipmi_password,
                "sdr",
                "list",
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=config.ipmi_timeout
            )

            if result.returncode == 0 and result.stdout.strip():
                # Count sensors
                sensor_lines = [
                    line
                    for line in result.stdout.split("\n")
                    if line.strip() and "|" in line
                ]
                sensor_count = len(sensor_lines)

                results.append(
                    ValidationResult(
                        check_name="ipmi_sensors",
                        status=ValidationStatus.PASS,
                        message=f"IPMI sensors accessible - {sensor_count} sensors found",
                        category=self.get_category(),
                        details={"sensor_count": sensor_count},
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="ipmi_sensors",
                        status=ValidationStatus.WARNING,
                        message="IPMI sensor access limited - may indicate OOB license issue",
                        category=self.get_category(),
                    )
                )

        except Exception as e:
            results.append(
                ValidationResult(
                    check_name="ipmi_sensors",
                    status=ValidationStatus.FAIL,
                    message=f"IPMI sensor test error: {e}",
                    category=self.get_category(),
                )
            )

        return results

    def _test_power_control(self, config: ValidationConfig) -> List[ValidationResult]:
        """Test IPMI power control functionality."""
        results = []

        try:
            cmd = [
                "ipmitool",
                "-I",
                "lanplus",
                "-H",
                config.ipmi_ip,
                "-U",
                config.ipmi_username,
                "-P",
                config.ipmi_password,
                "power",
                "status",
            ]

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=config.ipmi_timeout
            )

            if result.returncode == 0:
                power_status = result.stdout.strip()
                results.append(
                    ValidationResult(
                        check_name="ipmi_power_control",
                        status=ValidationStatus.PASS,
                        message=f"IPMI power control working - Status: {power_status}",
                        category=self.get_category(),
                        details={"power_status": power_status},
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="ipmi_power_control",
                        status=ValidationStatus.FAIL,
                        message="IPMI power control not accessible",
                        category=self.get_category(),
                        remediation="Check IPMI OOB license and permissions",
                    )
                )

        except Exception as e:
            results.append(
                ValidationResult(
                    check_name="ipmi_power_control",
                    status=ValidationStatus.FAIL,
                    message=f"Power control test error: {e}",
                    category=self.get_category(),
                )
            )

        return results

    def _extract_firmware_version(self, stdout: str) -> str:
        """Extract firmware version from IPMI mc info output."""
        for line in stdout.split("\n"):
            if "Firmware Revision" in line:
                return line.split(":")[-1].strip()
        return None
