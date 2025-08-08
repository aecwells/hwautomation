"""
Custom exceptions for orchestration workflows
."""


class WorkflowError(Exception):
    """Base exception for workflow errors."""

    pass


class CommissioningError(WorkflowError):
    """Raised when MaaS commissioning fails."""

    pass


class BiosConfigurationError(WorkflowError):
    """Raised when BIOS configuration fails."""

    pass


class IPMIConfigurationError(WorkflowError):
    """Raised when IPMI configuration fails."""

    pass


class SSHConnectionError(WorkflowError):
    """Raised when SSH connection fails."""

    pass


class ConfigurationValidationError(WorkflowError):
    """Raised when configuration validation fails."""

    pass
