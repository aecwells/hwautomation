"""
Test for the refactored provisioning system.

This test validates that the modular provisioning system works correctly
and maintains backward compatibility.
"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))

from hwautomation.orchestration.provisioning import (
    ProvisioningCoordinator,
    create_provisioning_workflow,
)
from hwautomation.orchestration.provisioning.base import (
    ProvisioningConfig,
    ProvisioningStage,
)
from hwautomation.orchestration.workflow_manager import WorkflowManager


class TestProvisioningRefactoring:
    """Test suite for the refactored provisioning system."""

    def test_provisioning_config_creation(self):
        """Test that ProvisioningConfig can be created with required parameters."""
        config = ProvisioningConfig(
            server_id="test-server-123", device_type="a1.c5.large"
        )

        assert config.server_id == "test-server-123"
        assert config.device_type == "a1.c5.large"
        assert config.target_ipmi_ip is None
        assert config.firmware_policy == "recommended"

    def test_provisioning_config_with_optional_params(self):
        """Test ProvisioningConfig with optional parameters."""
        config = ProvisioningConfig(
            server_id="test-server-456",
            device_type="d1.c2.medium",
            target_ipmi_ip="192.168.1.100",
            gateway="192.168.1.1",
            subnet_mask="255.255.255.0",
        )

        assert config.target_ipmi_ip == "192.168.1.100"
        assert config.gateway == "192.168.1.1"
        assert config.subnet_mask == "255.255.255.0"

    def test_provisioning_stages_enum(self):
        """Test that all expected provisioning stages are defined."""
        expected_stages = {
            "commissioning",
            "network_setup",
            "hardware_discovery",
            "bios_configuration",
            "ipmi_configuration",
            "finalization",
        }

        actual_stages = {stage.value for stage in ProvisioningStage}
        assert actual_stages == expected_stages

    @patch("hwautomation.orchestration.workflow_manager.WorkflowManager")
    def test_coordinator_creation(self, mock_workflow_manager):
        """Test that ProvisioningCoordinator can be created."""
        coordinator = ProvisioningCoordinator(mock_workflow_manager)

        assert coordinator.workflow_manager == mock_workflow_manager
        assert len(coordinator.stage_handlers) >= 3  # At least the implemented ones

    @patch("hwautomation.orchestration.workflow_manager.WorkflowManager")
    def test_workflow_creation_via_factory(self, mock_workflow_manager):
        """Test workflow creation via factory function."""
        # Mock the workflow manager
        mock_workflow = MagicMock()
        mock_workflow.id = "test-workflow-id"
        mock_workflow.steps = []
        mock_workflow_manager.create_workflow.return_value = mock_workflow

        # Create workflow
        workflow = create_provisioning_workflow(
            workflow_manager=mock_workflow_manager,
            server_id="test-server",
            device_type="a1.c5.large",
        )

        # Verify workflow was created
        assert workflow == mock_workflow
        mock_workflow_manager.create_workflow.assert_called_once()

    def test_stage_handlers_exist(self):
        """Test that required stage handlers are available."""
        mock_workflow_manager = MagicMock()
        coordinator = ProvisioningCoordinator(mock_workflow_manager)

        # Check that key stage handlers are implemented
        assert ProvisioningStage.COMMISSIONING in coordinator.stage_handlers
        assert ProvisioningStage.NETWORK_SETUP in coordinator.stage_handlers
        assert ProvisioningStage.HARDWARE_DISCOVERY in coordinator.stage_handlers

    def test_backward_compatibility_import(self):
        """Test that backward compatibility imports work."""
        try:
            from hwautomation.orchestration.server_provisioning_compat import (
                ServerProvisioningWorkflow,
            )

            assert ServerProvisioningWorkflow is not None
        except ImportError:
            pytest.fail("Backward compatibility import failed")

    def test_stage_timeout_configuration(self):
        """Test that stage timeouts are properly configured."""
        mock_workflow_manager = MagicMock()
        coordinator = ProvisioningCoordinator(mock_workflow_manager)

        # Test timeout configuration
        commissioning_timeout = coordinator._get_stage_timeout(
            ProvisioningStage.COMMISSIONING
        )
        network_timeout = coordinator._get_stage_timeout(
            ProvisioningStage.NETWORK_SETUP
        )

        assert commissioning_timeout == 1800  # 30 minutes
        assert network_timeout == 300  # 5 minutes

    def test_stage_retry_configuration(self):
        """Test that stage retry counts are properly configured."""
        mock_workflow_manager = MagicMock()
        coordinator = ProvisioningCoordinator(mock_workflow_manager)

        # Test retry configuration
        commissioning_retries = coordinator._get_stage_retry_count(
            ProvisioningStage.COMMISSIONING
        )
        network_retries = coordinator._get_stage_retry_count(
            ProvisioningStage.NETWORK_SETUP
        )

        assert commissioning_retries == 2
        assert network_retries == 3


if __name__ == "__main__":
    # Run basic functionality test
    print("🧪 Running provisioning refactoring tests...")

    test_suite = TestProvisioningRefactoring()

    try:
        test_suite.test_provisioning_config_creation()
        print("✅ Provisioning config creation test passed")

        test_suite.test_provisioning_config_with_optional_params()
        print("✅ Provisioning config with optional params test passed")

        test_suite.test_provisioning_stages_enum()
        print("✅ Provisioning stages enum test passed")

        test_suite.test_backward_compatibility_import()
        print("✅ Backward compatibility import test passed")

        print("\n🎉 All basic tests passed! Refactoring is working correctly.")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        exit(1)
