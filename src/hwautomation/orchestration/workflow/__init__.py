"""
Workflow Module

Modular workflow management system for hardware orchestration.

This module provides a clean separation of concerns for workflow management:
- Base definitions (enums, data classes, exceptions)
- Core workflow engine (execution, retry logic, cancellation)
- Firmware workflow handler (specialized firmware operations)
- Main workflow manager (coordination and lifecycle management)
- Workflow factory (standard workflow templates)

Usage:
    from hwautomation.orchestration.workflow import WorkflowManager, WorkflowFactory

    # Create manager
    manager = WorkflowManager(config)

    # Create workflow factory
    factory = WorkflowFactory(manager)

    # Create standard workflows
    workflow = factory.create_basic_provisioning_workflow(
        workflow_id="prov-001",
        server_id="server-123",
        device_type="a1.c5.large"
    )

    # Execute workflow
    context = manager.create_context(
        server_id="server-123",
        device_type="a1.c5.large"
    )
    success = workflow.execute(context)
"""

# Core components
from .base import (
    StepStatus,
    WorkflowCancellationError,
    WorkflowContext,
    WorkflowExecutionError,
    WorkflowStatus,
    WorkflowStep,
    WorkflowTimeoutError,
)
from .engine import Workflow
from .factory import WorkflowFactory
from .firmware import FirmwareWorkflowHandler
from .manager import WorkflowManager

# Convenience imports for backward compatibility
__all__ = [
    # Enums
    "WorkflowStatus",
    "StepStatus",
    # Data classes
    "WorkflowStep",
    "WorkflowContext",
    # Exceptions
    "WorkflowExecutionError",
    "WorkflowTimeoutError",
    "WorkflowCancellationError",
    # Core classes
    "Workflow",
    "WorkflowManager",
    "WorkflowFactory",
    "FirmwareWorkflowHandler",
]

# Version info
__version__ = "1.0.0"
__author__ = "HWAutomation Team"
__description__ = "Modular workflow management system for hardware orchestration"
