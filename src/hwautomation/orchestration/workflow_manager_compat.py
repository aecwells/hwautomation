"""
Workflow Manager Backward Compatibility Layer

This module provides backward compatibility for the original workflow_manager.py file.
It re-exports the modular components with the same interface to ensure existing code continues to work.

DEPRECATION NOTICE:
This compatibility layer is provided for transition purposes.
Please update your imports to use the new modular structure:

OLD:
    from hwautomation.orchestration.workflow_manager import WorkflowManager, Workflow

NEW:
    from hwautomation.orchestration.workflow import WorkflowManager, Workflow

This file will be removed in a future version.
"""

import warnings
from typing import Any, Dict

# Import all components from the new modular structure
from .workflow import (
    FirmwareWorkflowHandler,
    StepStatus,
    Workflow,
    WorkflowCancellationError,
    WorkflowContext,
    WorkflowExecutionError,
    WorkflowFactory,
    WorkflowManager,
    WorkflowStatus,
    WorkflowStep,
    WorkflowTimeoutError,
)

# Issue deprecation warning
warnings.warn(
    "Importing from 'workflow_manager' is deprecated. "
    "Please use 'from hwautomation.orchestration.workflow import ...' instead. "
    "This compatibility layer will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export everything for backward compatibility
__all__ = [
    "WorkflowManager",
    "Workflow",
    "WorkflowContext",
    "WorkflowStatus",
    "WorkflowStep",
    "StepStatus",
    "FirmwareWorkflowHandler",
    "WorkflowFactory",
    "WorkflowExecutionError",
    "WorkflowTimeoutError",
    "WorkflowCancellationError",
]

# Maintain the exact same interface as the original file
# This ensures that existing imports and usage patterns continue to work

# Legacy exception imports for compatibility
try:
    from ..exceptions import (
        BiosConfigurationError,
        CommissioningError,
        IPMIConfigurationError,
        SSHConnectionError,
        WorkflowError,
    )

    __all__.extend(
        [
            "BiosConfigurationError",
            "CommissioningError",
            "IPMIConfigurationError",
            "SSHConnectionError",
            "WorkflowError",
        ]
    )
except ImportError:
    # If exceptions module doesn't exist, define them here
    class WorkflowError(Exception):
        """Base workflow error for backward compatibility."""

        pass

    class BiosConfigurationError(WorkflowError):
        """BIOS configuration error for backward compatibility."""

        pass

    class CommissioningError(WorkflowError):
        """Commissioning error for backward compatibility."""

        pass

    class IPMIConfigurationError(WorkflowError):
        """IPMI configuration error for backward compatibility."""

        pass

    class SSHConnectionError(WorkflowError):
        """SSH connection error for backward compatibility."""

        pass


def create_workflow_manager(config: Dict[str, Any]) -> WorkflowManager:
    """
    Legacy factory function for creating WorkflowManager instances.

    Args:
        config: Configuration dictionary

    Returns:
        WorkflowManager instance
    """
    warnings.warn(
        "create_workflow_manager() is deprecated. "
        "Use WorkflowManager(config) directly instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return WorkflowManager(config)


# Legacy compatibility for direct imports
def get_workflow_manager():
    """Legacy function for backward compatibility."""
    warnings.warn(
        "get_workflow_manager() is deprecated. "
        "Create WorkflowManager instances directly.",
        DeprecationWarning,
        stacklevel=2,
    )
    return None
