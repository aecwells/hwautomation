"""
Workflow Manager for Hardware Orchestration

BACKWARD COMPATIBILITY LAYER - This file has been refactored into a modular structure.

The original workflow_manager.py has been split into multiple focused modules:
- workflow/base.py: Base definitions (enums, data classes, exceptions)
- workflow/engine.py: Core workflow execution engine
- workflow/manager.py: Main workflow manager
- workflow/firmware.py: Firmware workflow handler
- workflow/factory.py: Standard workflow templates

For new code, please use:
    from hwautomation.orchestration.workflow import WorkflowManager, Workflow

This file maintains backward compatibility but will show deprecation warnings.
"""

# Import everything from the compatibility layer
from .workflow_manager_compat import *
