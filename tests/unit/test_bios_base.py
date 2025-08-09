"""Tests for BIOS base classes and enums."""

import pytest

from src.hwautomation.hardware.bios.base import (
    BiosConfigResult,
    ConfigMethod,
    OperationStatus,
)


class TestConfigMethod:
    """Test ConfigMethod enum."""

    def test_config_method_values(self):
        """Test that ConfigMethod enum has expected values."""
        expected_values = {
            "redfish_standard",
            "redfish_oem",
            "vendor_tools",
            "hybrid",
            "manual",
        }
        actual_values = {method.value for method in ConfigMethod}
        assert actual_values == expected_values

    def test_config_method_redfish_standard(self):
        """Test ConfigMethod.REDFISH_STANDARD value."""
        assert ConfigMethod.REDFISH_STANDARD.value == "redfish_standard"

    def test_config_method_vendor_tools(self):
        """Test ConfigMethod.VENDOR_TOOLS value."""
        assert ConfigMethod.VENDOR_TOOLS.value == "vendor_tools"


class TestOperationStatus:
    """Test OperationStatus enum."""

    def test_operation_status_values(self):
        """Test that OperationStatus enum has expected values."""
        expected_values = {
            "pending",
            "running",
            "success",
            "failed",
            "partial",
            "cancelled",
        }
        actual_values = {status.value for status in OperationStatus}
        assert actual_values == expected_values

    def test_operation_status_success(self):
        """Test OperationStatus.SUCCESS value."""
        assert OperationStatus.SUCCESS.value == "success"

    def test_operation_status_failed(self):
        """Test OperationStatus.FAILED value."""
        assert OperationStatus.FAILED.value == "failed"


class TestBiosConfigResult:
    """Test BiosConfigResult dataclass."""

    def test_bios_config_result_creation(self):
        """Test creating a BiosConfigResult."""
        result = BiosConfigResult(
            success=True,
            method_used=ConfigMethod.REDFISH_STANDARD,
            settings_applied={"setting1": "value1"},
            settings_failed={"setting2": "error"},
        )

        assert result.success is True
        assert result.method_used == ConfigMethod.REDFISH_STANDARD
        assert result.settings_applied == {"setting1": "value1"}
        assert result.settings_failed == {"setting2": "error"}
        assert result.backup_file is None

    def test_bios_config_result_with_backup(self):
        """Test creating a BiosConfigResult with backup file."""
        result = BiosConfigResult(
            success=False,
            method_used=ConfigMethod.VENDOR_TOOLS,
            settings_applied={},
            settings_failed={"setting1": "timeout"},
            backup_file="/path/to/backup.xml",
        )

        assert result.success is False
        assert result.method_used == ConfigMethod.VENDOR_TOOLS
        assert result.settings_applied == {}
        assert result.settings_failed == {"setting1": "timeout"}
        assert result.backup_file == "/path/to/backup.xml"

    def test_bios_config_result_empty_settings(self):
        """Test creating a BiosConfigResult with empty settings."""
        result = BiosConfigResult(
            success=True,
            method_used=ConfigMethod.HYBRID,
            settings_applied={},
            settings_failed={},
        )

        assert result.success is True
        assert result.method_used == ConfigMethod.HYBRID
        assert result.settings_applied == {}
        assert result.settings_failed == {}
        assert result.backup_file is None
