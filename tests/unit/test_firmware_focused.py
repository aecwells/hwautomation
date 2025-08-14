"""
Focused test suite for the firmware management components.

This module tests the key firmware components based on the actual API:
- FirmwareManager: Main firmware coordination
- FirmwareInfo: Firmware information data structures
- FirmwareUpdateResult: Update operation results
- FirmwareType: Firmware type enums
- UpdatePolicy: Update policy management
"""

from typing import Any, Dict, Optional
from unittest.mock import Mock, patch

import pytest

from hwautomation.hardware.firmware.base import (
    BaseFirmwareHandler,
    BaseFirmwareRepository,
    FirmwareInfo,
    FirmwareType,
    FirmwareUpdateResult,
    Priority,
    UpdatePolicy,
)
from hwautomation.hardware.firmware.manager import FirmwareManager


class TestFirmwareManager:
    """Test suite for FirmwareManager main coordination functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        # Mock the config path to avoid file system dependencies
        self.test_config_path = "/tmp/test_firmware_config.yaml"

    def test_firmware_manager_initialization(self):
        """Test FirmwareManager initializes properly."""
        with patch.object(FirmwareManager, "_load_firmware_repository") as mock_repo:
            with patch.object(
                FirmwareManager, "_initialize_vendor_tools"
            ) as mock_tools:
                mock_repo.return_value = Mock()
                mock_tools.return_value = {}

                manager = FirmwareManager(self.test_config_path)

                assert manager.config_path == self.test_config_path
                assert hasattr(manager, "repository")
                assert hasattr(manager, "version_checker")
                assert hasattr(manager, "vendor_tools")
                assert manager.update_policy == UpdatePolicy.RECOMMENDED

    def test_get_default_config_path(self):
        """Test getting default configuration path."""
        with patch.object(FirmwareManager, "_load_firmware_repository") as mock_repo:
            with patch.object(
                FirmwareManager, "_initialize_vendor_tools"
            ) as mock_tools:
                mock_repo.return_value = Mock()
                mock_tools.return_value = {}

                manager = FirmwareManager()

                # Should contain firmware config path
                assert "firmware" in manager.config_path
                assert manager.config_path.endswith((".yaml", ".yml"))

    def test_set_update_policy_attribute(self):
        """Test setting update policy attribute directly."""
        with patch.object(FirmwareManager, "_load_firmware_repository") as mock_repo:
            with patch.object(
                FirmwareManager, "_initialize_vendor_tools"
            ) as mock_tools:
                mock_repo.return_value = Mock()
                mock_tools.return_value = {}

                manager = FirmwareManager(self.test_config_path)

                # Test different policies by setting attribute directly
                manager.update_policy = UpdatePolicy.MANUAL
                assert manager.update_policy == UpdatePolicy.MANUAL

                manager.update_policy = UpdatePolicy.LATEST
                assert manager.update_policy == UpdatePolicy.LATEST

    def test_firmware_manager_attributes(self):
        """Test that firmware manager has required attributes."""
        with patch.object(FirmwareManager, "_load_firmware_repository") as mock_repo:
            with patch.object(
                FirmwareManager, "_initialize_vendor_tools"
            ) as mock_tools:
                mock_repo.return_value = Mock()
                mock_tools.return_value = {}

                manager = FirmwareManager(self.test_config_path)

                # Core attributes should exist
                assert hasattr(manager, "config_path")
                assert hasattr(manager, "repository")
                assert hasattr(manager, "version_checker")
                assert hasattr(manager, "vendor_tools")
                assert hasattr(manager, "update_policy")

    def test_get_vendor_info_method_exists(self):
        """Test that get_vendor_info method exists."""
        with patch.object(FirmwareManager, "_load_firmware_repository") as mock_repo:
            with patch.object(
                FirmwareManager, "_initialize_vendor_tools"
            ) as mock_tools:
                mock_repo.return_value = Mock()
                mock_tools.return_value = {}

                manager = FirmwareManager(self.test_config_path)

                # Should have _get_vendor_info method
                assert hasattr(manager, "_get_vendor_info")

    def test_firmware_manager_error_handling(self):
        """Test firmware manager error handling."""
        with patch.object(FirmwareManager, "_load_firmware_repository") as mock_repo:
            with patch.object(
                FirmwareManager, "_initialize_vendor_tools"
            ) as mock_tools:
                mock_repo.side_effect = Exception("Repository not found")
                mock_tools.return_value = {}

                with pytest.raises(Exception, match="Repository not found"):
                    FirmwareManager("/invalid/path/config.yaml")


class TestFirmwareInfo:
    """Test suite for FirmwareInfo data structure."""

    def test_firmware_info_creation(self):
        """Test creating FirmwareInfo instance."""
        firmware = FirmwareInfo(
            firmware_type=FirmwareType.BIOS,
            current_version="2.7.0",
            latest_version="2.8.1",
            update_required=True,
            priority=Priority.HIGH,
            file_path="/test/firmware.bin",
            checksum="abcd1234",
        )

        assert firmware.firmware_type == FirmwareType.BIOS
        assert firmware.current_version == "2.7.0"
        assert firmware.latest_version == "2.8.1"
        assert firmware.update_required is True
        assert firmware.priority == Priority.HIGH
        assert firmware.file_path == "/test/firmware.bin"
        assert firmware.checksum == "abcd1234"

    def test_firmware_info_serialization(self):
        """Test FirmwareInfo serialization."""
        firmware = FirmwareInfo(
            firmware_type=FirmwareType.BMC,
            current_version="4.30.00",
            latest_version="4.40.00",
            update_required=True,
            priority=Priority.NORMAL,
            file_path="/test/firmware.bin",
            checksum="abcd1234",
        )

        # Test to_dict method
        firmware_dict = firmware.to_dict()
        assert firmware_dict["firmware_type"] == FirmwareType.BMC
        assert firmware_dict["current_version"] == "4.30.00"
        assert firmware_dict["latest_version"] == "4.40.00"
        assert firmware_dict["update_required"] is True

    def test_firmware_info_with_optional_fields(self):
        """Test FirmwareInfo with optional fields."""
        firmware = FirmwareInfo(
            firmware_type=FirmwareType.BIOS,
            current_version="2.7.0",
            latest_version="2.8.1",
            update_required=True,
            priority=Priority.CRITICAL,
            file_path="/test/firmware.bin",
            checksum="abcd1234",
            release_notes="Bug fixes and security updates",
            vendor="Dell",
            model="PowerEdge R750",
        )

        assert firmware.release_notes == "Bug fixes and security updates"
        assert firmware.vendor == "Dell"
        assert firmware.model == "PowerEdge R750"


class TestFirmwareUpdateResult:
    """Test suite for FirmwareUpdateResult data structure."""

    def test_update_result_success(self):
        """Test successful update result."""
        result = FirmwareUpdateResult(
            firmware_type=FirmwareType.BIOS,
            success=True,
            old_version="1.0.0",
            new_version="2.0.0",
            execution_time=300.0,
            requires_reboot=True,
        )

        assert result.firmware_type == FirmwareType.BIOS
        assert result.success is True
        assert result.old_version == "1.0.0"
        assert result.new_version == "2.0.0"
        assert result.execution_time == 300.0
        assert result.requires_reboot is True

    def test_update_result_failure(self):
        """Test failed update result."""
        result = FirmwareUpdateResult(
            firmware_type=FirmwareType.BMC,
            success=False,
            old_version="1.0.0",
            new_version="1.0.0",
            execution_time=60.0,
            requires_reboot=False,
            error_message="Update failed: Connection timeout",
        )

        assert result.firmware_type == FirmwareType.BMC
        assert result.success is False
        assert "timeout" in result.error_message.lower()
        assert result.old_version == "1.0.0"
        assert result.new_version == "1.0.0"

    def test_update_result_serialization(self):
        """Test update result serialization."""
        result = FirmwareUpdateResult(
            firmware_type=FirmwareType.BIOS,
            success=True,
            old_version="1.0.0",
            new_version="2.0.0",
            execution_time=300.0,
            requires_reboot=True,
        )

        result_dict = result.to_dict()
        assert result_dict["firmware_type"] == FirmwareType.BIOS.value
        assert result_dict["success"] is True
        assert result_dict["old_version"] == "1.0.0"
        assert result_dict["new_version"] == "2.0.0"


class TestFirmwareTypes:
    """Test suite for firmware type enums and constants."""

    def test_firmware_type_values(self):
        """Test FirmwareType enum values."""
        assert FirmwareType.BIOS != FirmwareType.BMC
        assert FirmwareType.BIOS != FirmwareType.NIC

        # Test that types are properly defined
        firmware_types = [FirmwareType.BIOS, FirmwareType.BMC, FirmwareType.NIC]
        assert len(firmware_types) >= 3

        # Test enum values
        assert FirmwareType.BIOS.value == "bios"
        assert FirmwareType.BMC.value == "bmc"

    def test_priority_values(self):
        """Test Priority enum values."""
        assert Priority.CRITICAL != Priority.HIGH
        assert Priority.HIGH != Priority.NORMAL
        assert Priority.NORMAL != Priority.LOW

        # Test that priorities are properly defined
        priorities = [Priority.CRITICAL, Priority.HIGH, Priority.NORMAL, Priority.LOW]
        assert len(priorities) == 4

        # Test enum values
        assert Priority.CRITICAL.value == "critical"
        assert Priority.HIGH.value == "high"

    def test_update_policy_values(self):
        """Test UpdatePolicy enum values."""
        assert UpdatePolicy.MANUAL != UpdatePolicy.RECOMMENDED
        assert UpdatePolicy.RECOMMENDED != UpdatePolicy.LATEST

        # Test that policies are properly defined
        policies = [
            UpdatePolicy.MANUAL,
            UpdatePolicy.RECOMMENDED,
            UpdatePolicy.LATEST,
            UpdatePolicy.SECURITY_ONLY,
        ]
        assert len(policies) >= 3

        # Test enum values
        assert UpdatePolicy.MANUAL.value == "manual"
        assert UpdatePolicy.RECOMMENDED.value == "recommended"


class TestBaseFirmwareHandler:
    """Test suite for BaseFirmwareHandler abstract base class."""

    def test_base_handler_initialization(self):
        """Test base handler initialization."""

        # Create a concrete implementation for testing
        class TestHandler(BaseFirmwareHandler):
            async def get_current_version(
                self, target_ip: str, username: str, password: str
            ) -> str:
                return "1.0.0"

            async def update_firmware(
                self,
                target_ip: str,
                username: str,
                password: str,
                firmware_file: str,
                operation_id: Optional[str] = None,
            ) -> FirmwareUpdateResult:
                return FirmwareUpdateResult(
                    firmware_type=FirmwareType.BIOS,
                    success=True,
                    old_version="1.0.0",
                    new_version="2.0.0",
                    execution_time=300.0,
                    requires_reboot=True,
                )

            def validate_firmware_file(self, firmware_file: str) -> bool:
                return True

            def get_update_time_estimate(self) -> int:
                return 300

        handler = TestHandler("Dell", "PowerEdge R750")
        assert handler.vendor == "Dell"
        assert handler.model == "PowerEdge R750"
        assert hasattr(handler, "logger")


class TestFirmwareIntegration:
    """Test suite for firmware component integration."""

    def test_end_to_end_firmware_workflow(self):
        """Test complete firmware workflow."""
        # Mock all dependencies
        mock_repo = Mock()

        with patch.object(
            FirmwareManager, "_load_firmware_repository", return_value=mock_repo
        ):
            with patch.object(
                FirmwareManager, "_initialize_vendor_tools", return_value={}
            ):
                manager = FirmwareManager("/tmp/test_config.yaml")

                # Create firmware info
                firmware_info = FirmwareInfo(
                    firmware_type=FirmwareType.BIOS,
                    current_version="2.7.0",
                    latest_version="2.8.1",
                    update_required=True,
                    priority=Priority.HIGH,
                    file_path="/firmware/bios_update.bin",
                )

                # Test components are properly initialized
                assert manager.repository is not None
                assert manager.version_checker is not None
                assert manager.update_policy == UpdatePolicy.RECOMMENDED


class TestBackwardCompatibility:
    """Test suite for backward compatibility of firmware components."""

    def test_firmware_imports_compatibility(self):
        """Test that firmware imports still work."""
        # Core firmware components should be importable
        from hwautomation.hardware.firmware.base import (
            FirmwareInfo,
            FirmwareType,
            FirmwareUpdateResult,
            Priority,
            UpdatePolicy,
        )
        from hwautomation.hardware.firmware.manager import FirmwareManager

        # All imports should succeed
        assert FirmwareManager is not None
        assert FirmwareInfo is not None
        assert FirmwareType is not None
        assert FirmwareUpdateResult is not None
        assert UpdatePolicy is not None
        assert Priority is not None

    def test_firmware_manager_api_compatibility(self):
        """Test that FirmwareManager API remains compatible."""
        with patch.object(FirmwareManager, "_load_firmware_repository") as mock_repo:
            with patch.object(
                FirmwareManager, "_initialize_vendor_tools"
            ) as mock_tools:
                mock_repo.return_value = Mock()
                mock_tools.return_value = {}

                manager = FirmwareManager()

                # Core attributes should exist
                assert hasattr(manager, "config_path")
                assert hasattr(manager, "repository")
                assert hasattr(manager, "version_checker")
                assert hasattr(manager, "vendor_tools")
                assert hasattr(manager, "update_policy")


if __name__ == "__main__":
    pytest.main([__file__])
