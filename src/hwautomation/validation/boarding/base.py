"""
Base classes and interfaces for the boarding validation system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ValidationStatus(Enum):
    """Validation status levels."""

    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


class ValidationCategory(Enum):
    """Categories of validation checks."""

    CONNECTIVITY = "connectivity"
    HARDWARE = "hardware"
    IPMI = "ipmi"
    BIOS = "bios"
    NETWORK = "network"
    CONFIGURATION = "configuration"


@dataclass
class ValidationResult:
    """Individual validation result."""

    check_name: str
    status: ValidationStatus
    message: str
    category: ValidationCategory
    details: Optional[Dict] = None
    remediation: Optional[str] = None


@dataclass
class ValidationConfig:
    """Configuration for boarding validation."""

    device_id: str
    device_type: str
    server_ip: str
    ipmi_ip: str
    ipmi_username: str = "ADMIN"
    ipmi_password: str = "ADMIN"
    ssh_username: str = "root"
    ssh_timeout: int = 30
    ipmi_timeout: int = 15


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

    def add_result(self, result: ValidationResult):
        """Add a validation result and update summary."""
        self.validations.append(result)
        self.update_summary()

    def get_results_by_category(
        self, category: ValidationCategory
    ) -> List[ValidationResult]:
        """Get validation results by category."""
        return [v for v in self.validations if v.category == category]

    def get_failed_results(self) -> List[ValidationResult]:
        """Get all failed validation results."""
        return [v for v in self.validations if v.status == ValidationStatus.FAIL]


class ValidationHandler(ABC):
    """Abstract base class for validation handlers."""

    @abstractmethod
    def get_category(self) -> ValidationCategory:
        """Get the validation category this handler manages."""
        pass

    @abstractmethod
    def validate(self, config: ValidationConfig) -> List[ValidationResult]:
        """Execute validation checks and return results."""
        pass

    @abstractmethod
    def get_required_prerequisites(self) -> List[ValidationCategory]:
        """Get list of validation categories that must pass before this one."""
        pass
