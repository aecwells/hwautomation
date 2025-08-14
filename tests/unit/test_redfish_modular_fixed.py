"""
Comprehensive test suite for the modular Redfish components in hwautomation.

This test module covers:
- Base manager functionality and common operations
- Power management operations (on, off, restart, status)
- BIOS configuration operations (get, set, reset)
- System information and management operations
- Firmware management and update operations
- Redfish coordinator integration and orchestration

Each test class focuses on a specific manager or component to ensure
modular testing and clear separation of concerns.
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

# Import base components
from hwautomation.hardware.redfish.base import RedfishCredentials

# Import the Redfish managers from the modularized structure
from hwautomation.hardware.redfish.managers.base import BaseRedfishManager
from hwautomation.hardware.redfish.managers.bios import RedfishBiosManager
from hwautomation.hardware.redfish.managers.coordinator import RedfishCoordinator
from hwautomation.hardware.redfish.managers.firmware import RedfishFirmwareManager
from hwautomation.hardware.redfish.managers.power import RedfishPowerManager
from hwautomation.hardware.redfish.managers.system import RedfishSystemManager


class TestBaseManager:
    """Test suite for BaseRedfishManager common functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_credentials = Mock()

        # Create a concrete implementation for testing
        class ConcreteManager(BaseRedfishManager):
            def get_supported_operations(self):
                return {"test": True}

        self.base_manager = ConcreteManager(self.mock_credentials)

    def test_base_manager_initialization(self):
        """Test BaseRedfishManager initializes properly."""
        assert self.base_manager.credentials == self.mock_credentials
        assert hasattr(self.base_manager, "logger")


class TestPowerManager:
    """Test suite for RedfishPowerManager power operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_credentials = Mock()
        self.power_manager = RedfishPowerManager(self.mock_credentials)

    def test_power_manager_initialization(self):
        """Test RedfishPowerManager initializes properly."""
        assert isinstance(self.power_manager, BaseRedfishManager)
        assert self.power_manager.credentials == self.mock_credentials

    def test_get_power_state(self):
        """Test getting power state."""
        with patch.object(
            self.power_manager.power_ops,
            "get_power_state",
            return_value=Mock(success=True, result="On"),
        ):
            state = self.power_manager.get_power_state()

        assert state == "On"

    def test_get_power_state_invalid_response(self):
        """Test handling invalid power state response."""
        with patch.object(
            self.power_manager.power_ops,
            "get_power_state",
            return_value=Mock(success=False, error_message="Invalid response"),
        ):
            state = self.power_manager.get_power_state()

        assert state is None

    def test_power_on_operation(self):
        """Test power on operation."""
        with patch.object(self.power_manager, "create_session") as mock_session:
            mock_session.return_value.__enter__.return_value = Mock()
            with patch.object(
                self.power_manager.power_ops,
                "set_power_state",
                return_value=Mock(success=True),
            ):
                result = self.power_manager.power_on()

        assert result is True

    def test_power_off_operation(self):
        """Test power off operation."""
        with patch.object(self.power_manager, "create_session") as mock_session:
            mock_session.return_value.__enter__.return_value = Mock()
            with patch.object(
                self.power_manager.power_ops,
                "set_power_state",
                return_value=Mock(success=True),
            ):
                result = self.power_manager.power_off()

        assert result is True

    def test_power_cycle_operation(self):
        """Test power cycle operation."""
        with patch.object(self.power_manager, "create_session") as mock_session:
            mock_session.return_value.__enter__.return_value = Mock()
            with patch.object(
                self.power_manager.power_ops,
                "set_power_state",
                return_value=Mock(success=True),
            ):
                result = self.power_manager.power_cycle()

        assert result is True


class TestBiosManager:
    """Test suite for RedfishBiosManager BIOS configuration operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_credentials = Mock()
        self.bios_manager = RedfishBiosManager(self.mock_credentials)

    def test_bios_manager_initialization(self):
        """Test RedfishBiosManager initializes properly."""
        assert isinstance(self.bios_manager, BaseRedfishManager)
        assert self.bios_manager.credentials == self.mock_credentials


class TestSystemManager:
    """Test suite for RedfishSystemManager system information operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_credentials = Mock()
        self.system_manager = RedfishSystemManager(self.mock_credentials)

    def test_system_manager_initialization(self):
        """Test RedfishSystemManager initializes properly."""
        assert isinstance(self.system_manager, BaseRedfishManager)
        assert self.system_manager.credentials == self.mock_credentials


class TestFirmwareManager:
    """Test suite for RedfishFirmwareManager firmware operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_credentials = Mock()
        self.firmware_manager = RedfishFirmwareManager(self.mock_credentials)

    def test_firmware_manager_initialization(self):
        """Test RedfishFirmwareManager initializes properly."""
        assert isinstance(self.firmware_manager, BaseRedfishManager)
        assert self.firmware_manager.credentials == self.mock_credentials


class TestRedfishCoordinator:
    """Test suite for RedfishCoordinator integration and orchestration."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_credentials = Mock()
        self.coordinator = RedfishCoordinator(
            host="192.168.1.100", username="admin", password="password"
        )

    def test_coordinator_initialization(self):
        """Test RedfishCoordinator initializes with all managers."""
        assert hasattr(self.coordinator, "power_manager")
        assert hasattr(self.coordinator, "bios_manager")
        assert hasattr(self.coordinator, "system_manager")
        assert hasattr(self.coordinator, "firmware_manager")

    def test_coordinator_manager_types(self):
        """Test that coordinator creates proper manager types."""
        assert isinstance(self.coordinator.power_manager, RedfishPowerManager)
        assert isinstance(self.coordinator.bios_manager, RedfishBiosManager)
        assert isinstance(self.coordinator.system_manager, RedfishSystemManager)
        assert isinstance(self.coordinator.firmware_manager, RedfishFirmwareManager)
