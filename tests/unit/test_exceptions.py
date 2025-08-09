"""Tests for exception classes and error handling."""

import pytest

from hwautomation.exceptions import (
    BiosConfigurationError,
    CommissioningError,
    ConfigurationValidationError,
    FirmwareDownloadError,
    FirmwareError,
    FirmwareUpdateException,
    FirmwareVerificationError,
    HWAutomationError,
    IPMIConfigurationError,
    SSHConnectionError,
    WorkflowError,
)


class TestHWAutomationError:
    """Test base HWAutomationError class."""

    def test_base_exception_creation(self):
        """Test creating base exception with message."""
        error = HWAutomationError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_base_exception_empty_message(self):
        """Test creating base exception with empty message."""
        error = HWAutomationError()
        assert str(error) == ""

    def test_base_exception_inheritance(self):
        """Test that HWAutomationError inherits from Exception."""
        error = HWAutomationError("test")
        assert isinstance(error, Exception)
        assert isinstance(error, HWAutomationError)


class TestWorkflowError:
    """Test WorkflowError class."""

    def test_workflow_error_creation(self):
        """Test creating workflow error."""
        error = WorkflowError("Workflow step failed")
        assert str(error) == "Workflow step failed"
        assert isinstance(error, HWAutomationError)
        assert isinstance(error, WorkflowError)

    def test_workflow_error_with_step(self):
        """Test workflow error with step information."""
        error = WorkflowError("Failed at step: BIOS Configuration")
        assert "Failed at step" in str(error)
        assert "BIOS Configuration" in str(error)


class TestCommissioningError:
    """Test CommissioningError class."""

    def test_commissioning_error_creation(self):
        """Test creating commissioning error."""
        error = CommissioningError("MaaS commissioning failed")
        assert str(error) == "MaaS commissioning failed"
        assert isinstance(error, WorkflowError)
        assert isinstance(error, CommissioningError)

    def test_commissioning_error_details(self):
        """Test commissioning error with details."""
        error = CommissioningError("Commission timeout after 300 seconds")
        assert "Commission timeout" in str(error)


class TestBiosConfigurationError:
    """Test BiosConfigurationError class."""

    def test_bios_configuration_error_creation(self):
        """Test creating BIOS configuration error."""
        error = BiosConfigurationError("BIOS setting update failed")
        assert str(error) == "BIOS setting update failed"
        assert isinstance(error, WorkflowError)
        assert isinstance(error, BiosConfigurationError)

    def test_bios_configuration_error_setting_specific(self):
        """Test BIOS configuration error with setting details."""
        error = BiosConfigurationError("Failed to set BootMode to UEFI")
        assert "Failed to set BootMode" in str(error)
        assert "UEFI" in str(error)


class TestIPMIConfigurationError:
    """Test IPMIConfigurationError class."""

    def test_ipmi_error_creation(self):
        """Test creating IPMI configuration error."""
        error = IPMIConfigurationError("IPMI setup failed")
        assert str(error) == "IPMI setup failed"
        assert isinstance(error, WorkflowError)
        assert isinstance(error, IPMIConfigurationError)

    def test_ipmi_error_device_specific(self):
        """Test IPMI error with device information."""
        error = IPMIConfigurationError("IPMI timeout for device 192.168.1.100")
        assert "IPMI timeout" in str(error)
        assert "192.168.1.100" in str(error)


class TestSSHConnectionError:
    """Test SSHConnectionError class."""

    def test_ssh_error_creation(self):
        """Test creating SSH connection error."""
        error = SSHConnectionError("SSH connection failed")
        assert str(error) == "SSH connection failed"
        assert isinstance(error, WorkflowError)
        assert isinstance(error, SSHConnectionError)

    def test_ssh_error_with_details(self):
        """Test SSH error with connection details."""
        error = SSHConnectionError("SSH timeout connecting to 192.168.1.50")
        assert "SSH timeout" in str(error)


class TestConfigurationValidationError:
    """Test ConfigurationValidationError class."""

    def test_validation_error_creation(self):
        """Test creating configuration validation error."""
        error = ConfigurationValidationError("Invalid configuration")
        assert str(error) == "Invalid configuration"
        assert isinstance(error, WorkflowError)
        assert isinstance(error, ConfigurationValidationError)

    def test_validation_error_field_specific(self):
        """Test validation error for specific field."""
        error = ConfigurationValidationError("Invalid IP address format: 192.168.1")
        assert "Invalid IP address format" in str(error)


class TestFirmwareError:
    """Test FirmwareError class."""

    def test_firmware_error_creation(self):
        """Test creating firmware error."""
        error = FirmwareError("Firmware update failed")
        assert str(error) == "Firmware update failed"
        assert isinstance(error, HWAutomationError)
        assert isinstance(error, FirmwareError)

    def test_firmware_update_exception(self):
        """Test FirmwareUpdateException."""
        error = FirmwareUpdateException("Update process failed")
        assert str(error) == "Update process failed"
        assert isinstance(error, FirmwareError)

    def test_firmware_download_error(self):
        """Test FirmwareDownloadError."""
        error = FirmwareDownloadError("Download failed from server")
        assert str(error) == "Download failed from server"
        assert isinstance(error, FirmwareError)

    def test_firmware_verification_error(self):
        """Test FirmwareVerificationError."""
        error = FirmwareVerificationError("Checksum mismatch")
        assert str(error) == "Checksum mismatch"
        assert isinstance(error, FirmwareError)


class TestExceptionInheritance:
    """Test exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_base(self):
        """Test that all custom exceptions inherit from HWAutomationError."""
        exceptions = [
            WorkflowError("test"),
            CommissioningError("test"),
            BiosConfigurationError("test"),
            IPMIConfigurationError("test"),
            SSHConnectionError("test"),
            ConfigurationValidationError("test"),
            FirmwareError("test"),
            FirmwareUpdateException("test"),
            FirmwareDownloadError("test"),
            FirmwareVerificationError("test"),
        ]

        for exception in exceptions:
            assert isinstance(exception, HWAutomationError)
            assert isinstance(exception, Exception)

    def test_workflow_specific_exceptions(self):
        """Test that workflow-specific exceptions inherit from WorkflowError."""
        workflow_errors = [
            CommissioningError("test"),
            BiosConfigurationError("test"),
            IPMIConfigurationError("test"),
            SSHConnectionError("test"),
            ConfigurationValidationError("test"),
        ]

        for error in workflow_errors:
            assert isinstance(error, WorkflowError)
            assert isinstance(error, HWAutomationError)

    def test_firmware_specific_exceptions(self):
        """Test that firmware-specific exceptions inherit from FirmwareError."""
        firmware_errors = [
            FirmwareUpdateException("test"),
            FirmwareDownloadError("test"),
            FirmwareVerificationError("test"),
        ]

        for error in firmware_errors:
            assert isinstance(error, FirmwareError)
            assert isinstance(error, HWAutomationError)


class TestExceptionUsage:
    """Test practical usage patterns for exceptions."""

    def test_exception_raising_and_catching(self):
        """Test raising and catching custom exceptions."""
        with pytest.raises(WorkflowError) as exc_info:
            raise WorkflowError("Missing config file")

        assert str(exc_info.value) == "Missing config file"

    def test_exception_chaining(self):
        """Test exception chaining with custom exceptions."""
        original_error = ValueError("Original error")

        with pytest.raises(WorkflowError) as exc_info:
            try:
                raise original_error
            except ValueError as e:
                raise WorkflowError("Workflow failed due to validation") from e

        assert str(exc_info.value) == "Workflow failed due to validation"
        assert exc_info.value.__cause__ is original_error

    def test_catching_base_exception(self):
        """Test catching specific exceptions via base class."""
        with pytest.raises(HWAutomationError):
            raise BiosConfigurationError("BIOS error")

        with pytest.raises(HWAutomationError):
            raise CommissioningError("Commissioning error")

    def test_exception_with_none_message(self):
        """Test exceptions with None message."""
        error = WorkflowError(None)
        assert str(error) == "None"

        error = FirmwareError()
        assert str(error) == ""
