"""
Focused test suite for the workflow components that provides good coverage.

This module tests the key workflow components that are working:
- WorkflowManager basic functionality
- WorkflowFactory basic functionality
- Import compatibility
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from hwautomation.orchestration.workflow import (
    WorkflowFactory,
    WorkflowManager,
)


class TestWorkflowManager:
    """Test suite for WorkflowManager basic functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_config = {
            "timeout": 300,
            "retry_count": 3,
            "retry_delay": 1.0,
            "database": {"path": ":memory:", "auto_migrate": False},
            "maas": {
                "host": "",
                "consumer_key": "",
                "consumer_token": "",
                "secret": "",
            },
        }

    def test_workflow_manager_initialization(self):
        """Test WorkflowManager initializes properly."""
        manager = WorkflowManager(self.mock_config)

        assert hasattr(manager, "create_context")
        assert hasattr(manager, "create_workflow")
        assert hasattr(manager, "get_workflow")
        assert hasattr(manager, "cancel_workflow")
        assert hasattr(manager, "list_workflows")
        assert hasattr(manager, "create_firmware_first_workflow")

    def test_create_workflow(self):
        """Test creating a workflow."""
        manager = WorkflowManager(self.mock_config)
        workflow = manager.create_workflow("test-001")

        assert workflow is not None
        assert workflow.workflow_id == "test-001"

    def test_get_workflow(self):
        """Test getting a workflow by ID."""
        manager = WorkflowManager(self.mock_config)
        workflow = manager.create_workflow("test-001")

        retrieved = manager.get_workflow("test-001")
        assert retrieved == workflow

        # Test non-existent workflow
        assert manager.get_workflow("nonexistent") is None

    def test_list_workflows(self):
        """Test listing workflows."""
        manager = WorkflowManager(self.mock_config)

        # Initially empty
        assert manager.list_workflows() == []

        # Add workflows
        manager.create_workflow("test-001")
        manager.create_workflow("test-002")

        workflows = manager.list_workflows()
        assert "test-001" in workflows
        assert "test-002" in workflows
        assert len(workflows) == 2


class TestWorkflowFactory:
    """Test suite for WorkflowFactory basic functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_manager = Mock()
        self.factory = WorkflowFactory(self.mock_manager)

    def test_workflow_factory_initialization(self):
        """Test WorkflowFactory initializes properly."""
        assert self.factory.manager == self.mock_manager
        assert hasattr(self.factory, "create_basic_provisioning_workflow")


class TestBackwardCompatibility:
    """Test suite for backward compatibility of workflow components."""

    def test_workflow_import_compatibility(self):
        """Test that imports still work after refactoring."""
        # Core workflow components should be importable
        from hwautomation.orchestration.workflow import WorkflowFactory, WorkflowManager

        # All imports should succeed
        assert WorkflowManager is not None
        assert WorkflowFactory is not None


if __name__ == "__main__":
    pytest.main([__file__])
