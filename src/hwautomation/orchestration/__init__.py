"""
Hardware Orchestration Module

This module provides end-to-end orchestration for server commissioning,
BIOS configuration, and IPMI setup workflows.

The module is organized into:
- workflows/: Modular workflow definitions and base abstractions
- steps/: Individual workflow step implementations
- utils/: Utility functions for orchestration operations
- Legacy modules for backward compatibility
"""

# Legacy imports for backward compatibility
from .device_selection import DeviceSelectionService, MachineFilter, MachineStatus
from .exceptions import (
    BiosConfigurationError,
    CommissioningError,
    IPMIConfigurationError,
    WorkflowError,
)
from .server_provisioning import ServerProvisioningWorkflow
from .workflow_manager import WorkflowManager

# New modular workflow components
from .workflows.base import (
    BaseWorkflow,
    BaseWorkflowStep,
    ConditionalWorkflowStep,
    RetryableWorkflowStep,
    StepContext,
    StepExecutionResult,
    StepResult,
    WorkflowStatus,
)
from .workflows.provisioning import (
    ServerProvisioningWorkflow as ModularServerProvisioningWorkflow,
    FirmwareFirstProvisioningWorkflow,
    create_provisioning_workflow,
    get_available_workflow_types,
)

# Utility modules
from .utils import SSHOperations, VendorDetector, WorkflowHelpers

__all__ = [
    # Legacy components
    "WorkflowManager",
    "ServerProvisioningWorkflow",
    "DeviceSelectionService",
    "MachineFilter",
    "MachineStatus",
    "WorkflowError",
    "CommissioningError",
    "BiosConfigurationError",
    "IPMIConfigurationError",
    
    # New modular components
    "BaseWorkflow",
    "BaseWorkflowStep", 
    "ConditionalWorkflowStep",
    "RetryableWorkflowStep",
    "StepContext",
    "StepExecutionResult",
    "StepResult",
    "WorkflowStatus",
    "ModularServerProvisioningWorkflow",
    "FirmwareFirstProvisioningWorkflow",
    "create_provisioning_workflow",
    "get_available_workflow_types",
    
    # Utilities
    "SSHOperations",
    "VendorDetector",
    "WorkflowHelpers",
]
