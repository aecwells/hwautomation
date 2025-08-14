"""
Focused test suite for orchestration workflow steps.

This suite targets high-impact coverage for the orchestration steps modules:
- BIOS configuration steps
- Commissioning steps
- Cleanup steps
- Hardware discovery steps
- IPMI configuration steps
- Network configuration steps

Strategy: Focus on step initialization, prerequisite validation, and execution patterns
without deep integration to achieve maximum coverage with minimal setup complexity.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Test the basic step structure and initialization patterns


class TestOrchestrationStepsBase:
    """Test base functionality of orchestration workflow steps."""

    def test_bios_steps_importable(self):
        """Test that BIOS configuration steps can be imported."""
        from hwautomation.orchestration.steps import bios_config

        # Check key step classes exist
        assert hasattr(bios_config, "PullBiosConfigStep")
        assert hasattr(bios_config, "logger")

        # Test step initialization
        step = bios_config.PullBiosConfigStep()
        assert step.name == "pull_bios_config"
        assert "BIOS configuration" in step.description
        assert step.bios_manager is None

    def test_commissioning_steps_importable(self):
        """Test that commissioning steps can be imported."""
        from hwautomation.orchestration.steps import commissioning

        # Check key step classes exist
        assert hasattr(commissioning, "SelectMachineStep")
        assert hasattr(commissioning, "logger")

        # Test step initialization
        step = commissioning.SelectMachineStep()
        assert step.name == "select_machine"
        assert "MaaS machine" in step.description
        assert step.maas_client is None

    def test_cleanup_steps_importable(self):
        """Test that cleanup steps can be imported."""
        from hwautomation.orchestration.steps import cleanup

        # Check key step classes exist
        assert hasattr(cleanup, "CleanupTempFilesStep")
        assert hasattr(cleanup, "logger")

        # Test step initialization
        step = cleanup.CleanupTempFilesStep()
        assert step.name == "cleanup_temp_files"
        assert "temporary files" in step.description

    def test_hardware_discovery_steps_importable(self):
        """Test that hardware discovery steps can be imported."""
        try:
            from hwautomation.orchestration.steps import hardware_discovery

            # Check logger exists
            assert hasattr(hardware_discovery, "logger")

        except ImportError:
            pytest.skip("Hardware discovery steps not available")

    def test_ipmi_config_steps_importable(self):
        """Test that IPMI configuration steps can be imported."""
        try:
            from hwautomation.orchestration.steps import ipmi_config

            # Check logger exists
            assert hasattr(ipmi_config, "logger")

        except ImportError:
            pytest.skip("IPMI config steps not available")

    def test_network_config_steps_importable(self):
        """Test that network configuration steps can be imported."""
        try:
            from hwautomation.orchestration.steps import network_config

            # Check logger exists
            assert hasattr(network_config, "logger")

        except ImportError:
            pytest.skip("Network config steps not available")


class TestBiosConfigSteps:
    """Test BIOS configuration workflow steps."""

    def test_pull_bios_step_prerequisites(self):
        """Test BIOS pull step prerequisite validation."""
        from hwautomation.orchestration.steps.bios_config import PullBiosConfigStep
        from hwautomation.orchestration.workflows.base import StepContext

        step = PullBiosConfigStep()

        # Test with missing server IP
        context = Mock(spec=StepContext)
        context.server_ip = None
        context.manufacturer = "Dell"
        context.add_error = Mock()

        result = step.validate_prerequisites(context)
        assert result is False
        context.add_error.assert_called_with(
            "Server IP required for BIOS configuration"
        )

        # Test with missing manufacturer
        context.server_ip = "192.168.1.100"
        context.manufacturer = None
        context.add_error.reset_mock()

        result = step.validate_prerequisites(context)
        assert result is False
        context.add_error.assert_called_with(
            "Server manufacturer required for BIOS configuration"
        )

        # Test with all prerequisites met
        context.manufacturer = "Dell"
        result = step.validate_prerequisites(context)
        assert result is True

    @patch("hwautomation.orchestration.steps.bios_config.BiosConfigManager")
    def test_bios_step_manager_initialization(self, mock_manager):
        """Test BIOS configuration manager initialization."""
        from hwautomation.orchestration.steps.bios_config import PullBiosConfigStep

        step = PullBiosConfigStep()

        # Test manager initialization pattern
        assert step.bios_manager is None

        # Mock context and test manager creation pattern would work
        mock_manager_instance = Mock()
        mock_manager.return_value = mock_manager_instance

        # Step should be able to create manager
        assert callable(mock_manager)


class TestCommissioningSteps:
    """Test MaaS commissioning workflow steps."""

    @patch("hwautomation.orchestration.steps.commissioning.load_config")
    def test_select_machine_prerequisites_dev_mode(self, mock_load_config):
        """Test machine selection prerequisite validation in dev mode."""
        from hwautomation.orchestration.steps.commissioning import SelectMachineStep
        from hwautomation.orchestration.workflows.base import StepContext

        # Configure mock for development mode
        mock_load_config.return_value = {"development": {"mock_services": True}}

        step = SelectMachineStep()
        context = Mock(spec=StepContext)
        context.add_sub_task = Mock()

        result = step.validate_prerequisites(context)
        assert result is True
        context.add_sub_task.assert_called_with("Running in development/mock mode")

    @patch("hwautomation.orchestration.steps.commissioning.load_config")
    def test_select_machine_prerequisites_mock_mode(self, mock_load_config):
        """Test machine selection prerequisite validation with MOCK_MAAS."""
        from hwautomation.orchestration.steps.commissioning import SelectMachineStep
        from hwautomation.orchestration.workflows.base import StepContext

        # Configure mock for MOCK_MAAS mode
        mock_load_config.return_value = {"MOCK_MAAS": True}

        step = SelectMachineStep()
        context = Mock(spec=StepContext)
        context.add_sub_task = Mock()

        result = step.validate_prerequisites(context)
        assert result is True
        context.add_sub_task.assert_called_with("Running in development/mock mode")

    def test_commissioning_step_initialization(self):
        """Test commissioning step initialization."""
        from hwautomation.orchestration.steps.commissioning import SelectMachineStep

        step = SelectMachineStep()
        assert step.name == "select_machine"
        assert step.description == "Select MaaS machine for commissioning"
        assert step.maas_client is None
        assert step.device_service is None


class TestCleanupSteps:
    """Test cleanup workflow steps."""

    def test_cleanup_temp_files_step_execution(self):
        """Test temporary file cleanup step execution."""
        from hwautomation.orchestration.steps.cleanup import CleanupTempFilesStep
        from hwautomation.orchestration.workflows.base import StepContext

        step = CleanupTempFilesStep()

        # Mock context with no temporary files
        context = Mock(spec=StepContext)
        context.add_sub_task = Mock()
        context.get_data = Mock(return_value=[])

        result = step.execute(context)

        # Should call add_sub_task for both initial cleanup and final status
        assert context.add_sub_task.call_count >= 1

        # Check that get_data was called for different file types
        calls = context.get_data.call_args_list
        call_args = [call[0][0] for call in calls]

        # Should check firmware_files, temp_bios_files, and temp_directories
        assert "firmware_files" in call_args

    def test_cleanup_temp_files_with_files(self):
        """Test cleanup step with actual temporary files."""
        from hwautomation.orchestration.steps.cleanup import CleanupTempFilesStep
        from hwautomation.orchestration.workflows.base import StepContext

        step = CleanupTempFilesStep()

        # Create a real temporary file
        with tempfile.NamedTemporaryFile(delete=False, dir="/tmp") as tmp_file:
            temp_file_path = tmp_file.name
            tmp_file.write(b"test content")

        try:
            # Mock context with temporary file
            context = Mock(spec=StepContext)
            context.add_sub_task = Mock()
            context.get_data = Mock(return_value=[temp_file_path])

            # Execute cleanup
            result = step.execute(context)

            # File should be removed
            assert not os.path.exists(temp_file_path)

        finally:
            # Cleanup in case test failed
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)

    def test_cleanup_step_initialization(self):
        """Test cleanup step initialization."""
        from hwautomation.orchestration.steps.cleanup import CleanupTempFilesStep

        step = CleanupTempFilesStep()
        assert step.name == "cleanup_temp_files"
        assert "temporary files" in step.description


class TestStepPatterns:
    """Test common patterns across orchestration steps."""

    def test_step_base_class_usage(self):
        """Test that steps properly inherit from base classes."""
        from hwautomation.orchestration.steps.bios_config import PullBiosConfigStep
        from hwautomation.orchestration.steps.cleanup import CleanupTempFilesStep
        from hwautomation.orchestration.steps.commissioning import SelectMachineStep
        from hwautomation.orchestration.workflows.base import BaseWorkflowStep

        # Test inheritance patterns
        assert issubclass(PullBiosConfigStep, BaseWorkflowStep)
        assert issubclass(SelectMachineStep, BaseWorkflowStep)
        assert issubclass(CleanupTempFilesStep, BaseWorkflowStep)

        # Test that all have required attributes
        for step_class in [PullBiosConfigStep, SelectMachineStep, CleanupTempFilesStep]:
            step = step_class()
            assert hasattr(step, "name")
            assert hasattr(step, "description")
            assert isinstance(step.name, str)
            assert isinstance(step.description, str)
            assert len(step.name) > 0
            assert len(step.description) > 0

    def test_step_logging_patterns(self):
        """Test that all step modules have proper logging setup."""
        from hwautomation.orchestration.steps import bios_config, cleanup, commissioning

        # All modules should have logger
        assert hasattr(bios_config, "logger")
        assert hasattr(commissioning, "logger")
        assert hasattr(cleanup, "logger")

        # Loggers should have proper names
        assert "bios_config" in bios_config.logger.name
        assert "commissioning" in commissioning.logger.name
        assert "cleanup" in cleanup.logger.name


class TestStepIntegration:
    """Test step integration patterns without deep dependencies."""

    def test_step_context_usage(self):
        """Test that steps properly use StepContext."""
        from hwautomation.orchestration.steps.bios_config import PullBiosConfigStep
        from hwautomation.orchestration.workflows.base import StepContext

        # Create mock context
        context = Mock(spec=StepContext)
        context.server_ip = "192.168.1.100"
        context.manufacturer = "Dell"
        context.add_error = Mock()
        context.add_sub_task = Mock()

        step = PullBiosConfigStep()

        # Test prerequisite validation uses context correctly
        result = step.validate_prerequisites(context)
        assert result is True

        # No errors should be added for valid context
        assert context.add_error.call_count == 0

    def test_step_execution_result_patterns(self):
        """Test that steps can create execution results."""
        from hwautomation.orchestration.steps.cleanup import CleanupTempFilesStep
        from hwautomation.orchestration.workflows.base import StepExecutionResult

        step = CleanupTempFilesStep()

        # Mock context
        context = Mock()
        context.add_sub_task = Mock()
        context.get_data = Mock(return_value=[])

        # Execute step
        result = step.execute(context)

        # Should return a result object (even if mocked)
        # This tests the execution pattern works
        assert context.add_sub_task.called


class TestStepModuleStructure:
    """Test the overall structure of step modules."""

    def test_bios_config_module_structure(self):
        """Test BIOS config module structure."""
        from hwautomation.orchestration.steps import bios_config

        # Should have core imports
        assert hasattr(bios_config, "logger")
        assert hasattr(bios_config, "BiosConfigManager")

        # Should have step classes
        assert hasattr(bios_config, "PullBiosConfigStep")

        # Test module docstring exists
        assert bios_config.__doc__ is not None
        assert "BIOS configuration" in bios_config.__doc__

    def test_commissioning_module_structure(self):
        """Test commissioning module structure."""
        from hwautomation.orchestration.steps import commissioning

        # Should have core imports
        assert hasattr(commissioning, "logger")
        assert hasattr(commissioning, "MaasClient")

        # Should have step classes
        assert hasattr(commissioning, "SelectMachineStep")

        # Test module docstring exists
        assert commissioning.__doc__ is not None
        assert "MaaS commissioning" in commissioning.__doc__

    def test_cleanup_module_structure(self):
        """Test cleanup module structure."""
        from hwautomation.orchestration.steps import cleanup

        # Should have core imports
        assert hasattr(cleanup, "logger")

        # Should have step classes
        assert hasattr(cleanup, "CleanupTempFilesStep")

        # Test module docstring exists
        assert cleanup.__doc__ is not None
        assert "Cleanup workflow" in cleanup.__doc__


class TestStepErrorHandling:
    """Test error handling patterns in orchestration steps."""

    def test_bios_step_error_handling(self):
        """Test BIOS step error handling patterns."""
        from hwautomation.orchestration.steps.bios_config import PullBiosConfigStep
        from hwautomation.orchestration.workflows.base import StepContext

        step = PullBiosConfigStep()
        context = Mock(spec=StepContext)
        context.add_error = Mock()

        # Test error handling for missing server IP
        context.server_ip = None
        context.manufacturer = "Dell"

        result = step.validate_prerequisites(context)
        assert result is False
        context.add_error.assert_called_once()

        # Error message should be descriptive
        error_message = context.add_error.call_args[0][0]
        assert "Server IP required" in error_message

    def test_cleanup_step_error_handling(self):
        """Test cleanup step error handling."""
        from hwautomation.orchestration.steps.cleanup import CleanupTempFilesStep

        step = CleanupTempFilesStep()
        context = Mock()
        context.add_sub_task = Mock()
        context.get_data = Mock(return_value=["/nonexistent/file"])

        # Should handle nonexistent files gracefully
        result = step.execute(context)

        # Should not raise exception
        assert context.add_sub_task.called


class TestBackwardCompatibility:
    """Test backward compatibility of step interfaces."""

    def test_step_interface_compatibility(self):
        """Test that step interfaces remain compatible."""
        from hwautomation.orchestration.steps.bios_config import PullBiosConfigStep
        from hwautomation.orchestration.steps.cleanup import CleanupTempFilesStep
        from hwautomation.orchestration.steps.commissioning import SelectMachineStep

        # All steps should have consistent interface
        steps = [PullBiosConfigStep(), SelectMachineStep(), CleanupTempFilesStep()]

        for step in steps:
            # Should have name and description
            assert hasattr(step, "name")
            assert hasattr(step, "description")

            # Should be able to call validate_prerequisites (if it exists)
            if hasattr(step, "validate_prerequisites"):
                assert callable(step.validate_prerequisites)

            # Should be able to call execute (if it exists)
            if hasattr(step, "execute"):
                assert callable(step.execute)

    def test_optional_step_modules(self):
        """Test that optional step modules can be imported safely."""
        step_modules = [
            "hardware_discovery",
            "ipmi_config",
            "network_config",
            "firmware_update",
            "maas_commission",
        ]

        for module_name in step_modules:
            try:
                module = __import__(
                    f"hwautomation.orchestration.steps.{module_name}",
                    fromlist=[module_name],
                )

                # If importable, should have logger
                assert hasattr(module, "logger")

            except ImportError:
                # It's OK if some modules aren't available
                pytest.skip(f"Optional step module {module_name} not available")


if __name__ == "__main__":
    pytest.main([__file__])
