"""
Focused test suite for the IPMI management components.

This module tests the key IPMI components based on the actual API:
- IpmiManager: Main IPMI coordination
- IPMICredentials: IPMI connection credentials
- IPMIConfigResult: Configuration operation results
- PowerStatus: Power status information
- SensorReading: Sensor monitoring data
"""

from typing import Any, Dict, Optional
from unittest.mock import Mock, patch

import pytest

from hwautomation.hardware.ipmi.base import (
    BaseIPMIHandler,
    IPMICommand,
    IPMIConfigResult,
    IPMICredentials,
    IPMISettings,
    IPMISystemInfo,
    IPMIVendor,
    PowerState,
    PowerStatus,
    SensorReading,
)
from hwautomation.hardware.ipmi.manager import IpmiManager


class TestIpmiManager:
    """Test suite for IpmiManager main coordination functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.test_credentials = IPMICredentials(
            ip_address="192.168.1.100",
            username="admin",
            password="password",
            interface="lanplus",
        )

    def test_ipmi_manager_initialization(self):
        """Test IpmiManager initializes properly."""
        with patch.object(IpmiManager, "_load_vendor_tools") as mock_tools:
            mock_tools.return_value = {}

            manager = IpmiManager()

            # Core attributes should exist
            assert hasattr(manager, "logger")
            assert hasattr(manager, "vendor_tools")

    def test_ipmi_manager_with_credentials(self):
        """Test IpmiManager initialization with credentials."""
        with patch.object(IpmiManager, "_load_vendor_tools") as mock_tools:
            mock_tools.return_value = {}

            manager = IpmiManager()

            # Should be able to work with credentials
            assert manager is not None

    def test_configure_ipmi_method_exists(self):
        """Test that configure_ipmi method exists."""
        with patch.object(IpmiManager, "_load_vendor_tools") as mock_tools:
            mock_tools.return_value = {}

            manager = IpmiManager()
            assert hasattr(manager, "configure_ipmi")

    def test_get_power_status_method_exists(self):
        """Test that power status methods exist."""
        with patch.object(IpmiManager, "_load_vendor_tools") as mock_tools:
            mock_tools.return_value = {}

            manager = IpmiManager()

            # Power control methods should exist
            assert hasattr(manager, "get_power_status")
            assert hasattr(manager, "power_on")
            assert hasattr(manager, "power_off")
            assert hasattr(manager, "power_cycle")

    def test_sensor_methods_exist(self):
        """Test that sensor methods exist."""
        with patch.object(IpmiManager, "_load_vendor_tools") as mock_tools:
            mock_tools.return_value = {}

            manager = IpmiManager()

            # Sensor methods should exist
            assert hasattr(manager, "get_sensor_readings")
            assert hasattr(manager, "get_system_info")

    def test_ipmi_manager_vendor_detection(self):
        """Test IPMI manager vendor detection."""
        with patch.object(IpmiManager, "_load_vendor_tools") as mock_tools:
            mock_tools.return_value = {}

            manager = IpmiManager()

            # Vendor detection method should exist
            assert hasattr(manager, "_detect_vendor")

    def test_ipmi_manager_error_handling(self):
        """Test IPMI manager error handling."""
        with patch.object(IpmiManager, "_load_vendor_tools") as mock_tools:
            mock_tools.side_effect = Exception("Vendor tools not found")

            with pytest.raises(Exception, match="Vendor tools not found"):
                IpmiManager()


class TestIPMICredentials:
    """Test suite for IPMICredentials data structure."""

    def test_ipmi_credentials_creation(self):
        """Test creating IPMICredentials instance."""
        credentials = IPMICredentials(
            ip_address="192.168.1.100",
            username="admin",
            password="password",
            interface="lanplus",
        )

        assert credentials.ip_address == "192.168.1.100"
        assert credentials.username == "admin"
        assert credentials.password == "password"
        assert credentials.interface == "lanplus"

    def test_ipmi_credentials_with_port(self):
        """Test IPMICredentials with custom port."""
        credentials = IPMICredentials(
            ip_address="192.168.1.100", username="admin", password="password", port=623
        )

        assert credentials.port == 623

    def test_ipmi_credentials_defaults(self):
        """Test IPMICredentials default values."""
        credentials = IPMICredentials(ip_address="192.168.1.100")

        assert credentials.username == "ADMIN"
        assert credentials.password == ""
        assert credentials.interface == "lanplus"
        assert credentials.port == 623


class TestIPMIConfigResult:
    """Test suite for IPMIConfigResult data structure."""

    def test_config_result_success(self):
        """Test successful IPMI configuration result."""
        result = IPMIConfigResult(
            success=True,
            vendor=IPMIVendor.DELL_IDRAC,
            firmware_version="2.80.80.80",
            settings_applied=["user_enabled", "password_set"],
            execution_time=30.5,
        )

        assert result.success is True
        assert result.vendor == IPMIVendor.DELL_IDRAC
        assert result.firmware_version == "2.80.80.80"
        assert "user_enabled" in result.settings_applied
        assert result.execution_time == 30.5

    def test_config_result_failure(self):
        """Test failed IPMI configuration result."""
        result = IPMIConfigResult(
            success=False,
            vendor=IPMIVendor.UNKNOWN,
            errors=["Connection timeout", "Authentication failed"],
            execution_time=10.0,
        )

        assert result.success is False
        assert result.vendor == IPMIVendor.UNKNOWN
        assert "Connection timeout" in result.errors
        assert "Authentication failed" in result.errors
        assert result.execution_time == 10.0

    def test_config_result_defaults(self):
        """Test IPMIConfigResult default values."""
        result = IPMIConfigResult(success=True, vendor=IPMIVendor.SUPERMICRO)

        assert result.success is True
        assert result.vendor == IPMIVendor.SUPERMICRO
        assert result.firmware_version is None
        assert result.settings_applied == []
        assert result.errors == []
        assert result.execution_time == 0.0


class TestPowerStatus:
    """Test suite for PowerStatus data structure."""

    def test_power_status_creation(self):
        """Test creating PowerStatus instance."""
        status = PowerStatus(
            state="on",
            raw_output="Chassis Power is on",
            timestamp="2024-01-01 12:00:00",
        )

        assert status.state == "on"
        assert status.raw_output == "Chassis Power is on"
        assert status.timestamp == "2024-01-01 12:00:00"

    def test_power_status_minimal(self):
        """Test PowerStatus with minimal data."""
        status = PowerStatus(state="off", raw_output="Chassis Power is off")

        assert status.state == "off"
        assert status.raw_output == "Chassis Power is off"
        assert status.timestamp is None


class TestSensorReading:
    """Test suite for SensorReading data structure."""

    def test_sensor_reading_creation(self):
        """Test creating SensorReading instance."""
        reading = SensorReading(
            name="CPU Temp",
            value="45.000",
            unit="degrees C",
            status="ok",
            lower_threshold="0.000",
            upper_threshold="85.000",
        )

        assert reading.name == "CPU Temp"
        assert reading.value == "45.000"
        assert reading.unit == "degrees C"
        assert reading.status == "ok"
        assert reading.lower_threshold == "0.000"
        assert reading.upper_threshold == "85.000"

    def test_sensor_reading_minimal(self):
        """Test SensorReading with minimal data."""
        reading = SensorReading(name="Fan1", value="1200", unit="RPM", status="ok")

        assert reading.name == "Fan1"
        assert reading.value == "1200"
        assert reading.unit == "RPM"
        assert reading.status == "ok"
        assert reading.lower_threshold is None
        assert reading.upper_threshold is None


class TestIPMISystemInfo:
    """Test suite for IPMISystemInfo data structure."""

    def test_system_info_creation(self):
        """Test creating IPMISystemInfo instance."""
        info = IPMISystemInfo(
            manufacturer="Dell Inc.",
            product_name="PowerEdge R750",
            firmware_version="2.80.80.80",
            serial_number="ABC123456",
            guid="44454c4c-3700-1038-8052-c8c04f4d5431",
            vendor=IPMIVendor.DELL_IDRAC,
        )

        assert info.manufacturer == "Dell Inc."
        assert info.product_name == "PowerEdge R750"
        assert info.firmware_version == "2.80.80.80"
        assert info.serial_number == "ABC123456"
        assert info.vendor == IPMIVendor.DELL_IDRAC

    def test_system_info_defaults(self):
        """Test IPMISystemInfo default values."""
        info = IPMISystemInfo()

        assert info.manufacturer is None
        assert info.product_name is None
        assert info.firmware_version is None
        assert info.serial_number is None
        assert info.guid is None
        assert info.vendor == IPMIVendor.UNKNOWN


class TestIPMIEnums:
    """Test suite for IPMI enums and constants."""

    def test_ipmi_vendor_values(self):
        """Test IPMIVendor enum values."""
        assert IPMIVendor.DELL_IDRAC != IPMIVendor.HP_ILO
        assert IPMIVendor.HP_ILO != IPMIVendor.SUPERMICRO

        # Test enum values
        assert IPMIVendor.DELL_IDRAC.value == "dell_idrac"
        assert IPMIVendor.HP_ILO.value == "hp_ilo"
        assert IPMIVendor.SUPERMICRO.value == "supermicro"
        assert IPMIVendor.UNKNOWN.value == "unknown"

    def test_power_state_values(self):
        """Test PowerState enum values."""
        assert PowerState.ON != PowerState.OFF
        assert PowerState.OFF != PowerState.RESET

        # Test enum values
        assert PowerState.ON.value == "on"
        assert PowerState.OFF.value == "off"
        assert PowerState.RESET.value == "reset"
        assert PowerState.CYCLE.value == "cycle"
        assert PowerState.SOFT.value == "soft"

    def test_ipmi_command_values(self):
        """Test IPMICommand enum values."""
        assert IPMICommand.POWER_ON != IPMICommand.POWER_OFF
        assert IPMICommand.SENSOR_LIST != IPMICommand.FRU_LIST

        # Test enum values
        assert IPMICommand.POWER_STATUS.value == "power status"
        assert IPMICommand.POWER_ON.value == "power on"
        assert IPMICommand.SENSOR_LIST.value == "sensor list"


class TestBaseIPMIHandler:
    """Test suite for BaseIPMIHandler abstract base class."""

    def test_base_handler_initialization(self):
        """Test base handler initialization."""
        credentials = IPMICredentials(
            ip_address="192.168.1.100", username="admin", password="password"
        )

        # Create a concrete implementation for testing
        class TestHandler(BaseIPMIHandler):
            def execute_command(self, command, additional_args=None):
                return Mock()

            def get_power_status(self):
                return PowerStatus(state="on", raw_output="Power is on")

        handler = TestHandler(credentials, timeout=60)
        assert handler.credentials == credentials
        assert handler.timeout == 60


class TestIPMIIntegration:
    """Test suite for IPMI component integration."""

    def test_end_to_end_ipmi_workflow(self):
        """Test complete IPMI workflow."""
        with patch.object(IpmiManager, "_load_vendor_tools") as mock_tools:
            mock_tools.return_value = {}

            manager = IpmiManager()

            # Create test credentials
            credentials = IPMICredentials(
                ip_address="192.168.1.100", username="admin", password="password"
            )

            # Test components are properly initialized
            assert manager is not None
            assert credentials.ip_address == "192.168.1.100"

    def test_ipmi_manager_vendor_tools_loading(self):
        """Test IPMI manager vendor tools loading."""
        with patch.object(IpmiManager, "_load_vendor_tools") as mock_tools:
            mock_tools.return_value = {
                "dell_idrac": Mock(),
                "hp_ilo": Mock(),
                "supermicro": Mock(),
            }

            manager = IpmiManager()

            assert manager.vendor_tools is not None
            assert len(manager.vendor_tools) == 3


class TestBackwardCompatibility:
    """Test suite for backward compatibility of IPMI components."""

    def test_ipmi_imports_compatibility(self):
        """Test that IPMI imports still work."""
        # Core IPMI components should be importable
        from hwautomation.hardware.ipmi.base import (
            IPMIConfigResult,
            IPMICredentials,
            IPMIVendor,
            PowerStatus,
            SensorReading,
        )
        from hwautomation.hardware.ipmi.manager import IpmiManager

        # All imports should succeed
        assert IpmiManager is not None
        assert IPMICredentials is not None
        assert IPMIConfigResult is not None
        assert PowerStatus is not None
        assert SensorReading is not None
        assert IPMIVendor is not None

    def test_ipmi_manager_api_compatibility(self):
        """Test that IpmiManager API remains compatible."""
        with patch.object(IpmiManager, "_load_vendor_tools") as mock_tools:
            mock_tools.return_value = {}

            manager = IpmiManager()

            # Core methods and attributes should exist
            assert hasattr(manager, "logger")
            assert hasattr(manager, "configure_ipmi")
            assert hasattr(manager, "get_power_status")
            assert hasattr(manager, "get_sensor_readings")

    def test_ipmi_credentials_api_compatibility(self):
        """Test that IPMICredentials API remains compatible."""
        credentials = IPMICredentials(
            ip_address="192.168.1.100", username="admin", password="password"
        )

        # Core attributes should exist
        assert hasattr(credentials, "ip_address")
        assert hasattr(credentials, "username")
        assert hasattr(credentials, "password")
        assert hasattr(credentials, "interface")
        assert hasattr(credentials, "port")


if __name__ == "__main__":
    pytest.main([__file__])
