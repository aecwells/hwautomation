"""
Shared exceptions for the HWAutomation package

This module contains common exceptions that are used across multiple modules
to avoid circular import issues.
"""


class HWAutomationError(Exception):
    """Base exception for all HWAutomation errors"""

    pass


class WorkflowError(HWAutomationError):
    """Base exception for workflow errors"""

    pass


class CommissioningError(WorkflowError):
    """Raised when MaaS commissioning fails"""

    pass


class BiosConfigurationError(WorkflowError):
    """Raised when BIOS configuration fails"""

    pass


class IPMIConfigurationError(WorkflowError):
    """Raised when IPMI configuration fails"""

    pass


class SSHConnectionError(WorkflowError):
    """Raised when SSH connection fails"""

    pass


class ConfigurationValidationError(WorkflowError):
    """Raised when configuration validation fails"""

    pass


class FirmwareError(HWAutomationError):
    """Base exception for firmware-related errors"""

    pass


class FirmwareUpdateException(FirmwareError):
    """Raised when firmware update fails"""

    pass


class FirmwareDownloadError(FirmwareError):
    """Raised when firmware download fails"""

    pass


class FirmwareVerificationError(FirmwareError):
    """Raised when firmware verification fails"""

    pass
