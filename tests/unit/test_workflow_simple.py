"""
Test suite for the workflow components in hwautomation.orchestration.workflow.

This module tests the existing workflow components:
- WorkflowManager: Main workflow management
- WorkflowFactory: Creation of standard workflow types
- WorkflowContext: Context management and data sharing
- Workflow: Core workflow execution engine
- FirmwareWorkflowHandler: Specialized firmware operations
"""

import threading
import time
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest

from hwautomation.orchestration.workflow import (
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


class TestWorkflowManager:
    """Test suite for WorkflowManager main management functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = {"timeout": 300, "retry_count": 3, "retry_delay": 1.0}

    def test_workflow_manager_initialization(self):
        """Test WorkflowManager initializes properly."""
        manager = WorkflowManager(self.mock_config)

        assert hasattr(manager, "create_context")
        assert hasattr(manager, "create_workflow")
        assert hasattr(manager, "get_workflow")
        assert hasattr(manager, "cancel_workflow")
        assert hasattr(manager, "list_workflows")
        assert hasattr(manager, "create_firmware_first_workflow")

    def test_create_workflow_context(self):
        """Test creating workflow context through manager."""
        manager = WorkflowManager(self.mock_config)

        context = manager.create_context(
            server_id="server-123", device_type="a1.c5.large"
        )

        assert isinstance(context, WorkflowContext)
        assert context.server_id == "server-123"
        assert context.device_type == "a1.c5.large"


class TestWorkflowFactory:
    """Test suite for WorkflowFactory workflow creation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_manager = Mock()
        self.factory = WorkflowFactory(self.mock_manager)

    def test_workflow_factory_initialization(self):
        """Test WorkflowFactory initializes properly."""
        assert self.factory.manager == self.mock_manager
        assert hasattr(self.factory, "create_basic_provisioning_workflow")


class TestWorkflowContext:
    """Test suite for WorkflowContext context management."""

    def setup_method(self):
        """Set up test fixtures."""
        from unittest.mock import Mock

        self.context = WorkflowContext(
            server_id="server-123",
            device_type="a1.c5.large",
            target_ipmi_ip="192.168.1.100",
            rack_location="rack-1",
            maas_client=Mock(),
            db_helper=Mock(),
        )

    def test_workflow_context_initialization(self):
        """Test WorkflowContext initialization and basic functionality."""
        # Test basic initialization
        assert self.context.server_id == "server-123"
        assert self.context.device_type == "a1.c5.large"
        assert self.context.target_ipmi_ip == "192.168.1.100"
        assert self.context.rack_location == "rack-1"

        # Test available methods
        assert hasattr(self.context, "report_sub_task")

        # Test metadata manipulation
        assert isinstance(self.context.metadata, dict)
        self.context.metadata["test_key"] = "test_value"
        assert self.context.metadata["test_key"] == "test_value"


class TestWorkflow:
    """Test suite for Workflow execution engine."""

    def setup_method(self):
        """Set up test fixtures."""
        self.workflow_id = "test-001"
        self.server_id = "server-123"
        self.device_type = "a1.c5.large"

        # Create a mock workflow manager
        self.mock_manager = Mock()

        # Create test steps
        self.test_steps = [
            WorkflowStep(
                name="Test Step 1",
                description="First test step",
                function=lambda ctx: True,
                timeout=60,
            ),
            WorkflowStep(
                name="Test Step 2",
                description="Second test step",
                function=lambda ctx: True,
                timeout=120,
            ),
        ]

        self.workflow = Workflow(
            workflow_id=self.workflow_id, manager=self.mock_manager
        )

        # Add steps to workflow
        for step in self.test_steps:
            self.workflow.add_step(step)

    def test_workflow_initialization(self):
        """Test Workflow initializes properly."""
        assert self.workflow.id == self.workflow_id
        assert len(self.workflow.steps) == 2
        assert self.workflow.status == WorkflowStatus.PENDING
        assert self.workflow.manager == self.mock_manager


class TestFirmwareWorkflowHandler:
    """Test suite for FirmwareWorkflowHandler specialized firmware operations."""

    def setup_method(self):
        """Set up test fixtures."""
        from unittest.mock import Mock

        mock_config = {"firmware": {"enabled": True}}
        self.handler = FirmwareWorkflowHandler(mock_config)

    def test_firmware_handler_initialization(self):
        """Test FirmwareWorkflowHandler initializes properly."""
        assert hasattr(self.handler, "create_firmware_first_workflow")
        assert hasattr(self.handler, "initialize_firmware_components")
        assert hasattr(self.handler, "is_firmware_available")


class TestBackwardCompatibility:
    """Test suite for backward compatibility of workflow components."""

    def test_workflow_import_compatibility(self):
        """Test that imports still work after refactoring."""
        # Core workflow components should be importable
        from hwautomation.orchestration.workflow import (
            Workflow,
            WorkflowContext,
            WorkflowFactory,
            WorkflowManager,
        )

        # All imports should succeed
        assert WorkflowManager is not None
        assert WorkflowFactory is not None
        assert WorkflowContext is not None
        assert Workflow is not None


if __name__ == "__main__":
    pytest.main([__file__])
