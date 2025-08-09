"""Tests for hardware discovery base classes."""

from dataclasses import asdict
from unittest.mock import Mock, patch

import pytest

from hwautomation.hardware.discovery.base import (
    BaseParser,
    BaseVendorDiscovery,
    HardwareDiscovery,
    IPMIInfo,
    NetworkInterface,
    SystemInfo,
)


class TestNetworkInterface:
    """Test NetworkInterface dataclass."""

    def test_network_interface_creation(self):
        """Test creating a NetworkInterface instance."""
        interface = NetworkInterface(
            name="eth0",
            mac_address="00:11:22:33:44:55",
            ip_address="192.168.1.100",
            netmask="255.255.255.0",
            state="up",
        )
        assert interface.name == "eth0"
        assert interface.mac_address == "00:11:22:33:44:55"
        assert interface.ip_address == "192.168.1.100"
        assert interface.netmask == "255.255.255.0"
        assert interface.state == "up"

    def test_network_interface_minimal(self):
        """Test creating NetworkInterface with minimal data."""
        interface = NetworkInterface(
            name="eth1",
            mac_address="00:11:22:33:44:66",
        )
        assert interface.name == "eth1"
        assert interface.mac_address == "00:11:22:33:44:66"
        assert interface.ip_address is None
        assert interface.netmask is None
        assert interface.state == "unknown"

    def test_network_interface_serialization(self):
        """Test NetworkInterface serialization to dict."""
        interface = NetworkInterface(
            name="eth0",
            mac_address="00:11:22:33:44:55",
        )
        data = asdict(interface)
        assert data["name"] == "eth0"
        assert data["mac_address"] == "00:11:22:33:44:55"
        assert data["state"] == "unknown"


class TestIPMIInfo:
    """Test IPMIInfo dataclass."""

    def test_ipmi_info_creation(self):
        """Test creating an IPMIInfo instance."""
        ipmi = IPMIInfo(
            ip_address="192.168.2.100",
            mac_address="00:aa:bb:cc:dd:ee",
            gateway="192.168.2.1",
            netmask="255.255.255.0",
            vlan_id=100,
            channel=1,
            enabled=True,
        )
        assert ipmi.ip_address == "192.168.2.100"
        assert ipmi.mac_address == "00:aa:bb:cc:dd:ee"
        assert ipmi.gateway == "192.168.2.1"
        assert ipmi.vlan_id == 100
        assert ipmi.channel == 1
        assert ipmi.enabled is True

    def test_ipmi_info_defaults(self):
        """Test IPMIInfo with default values."""
        ipmi = IPMIInfo()
        assert ipmi.ip_address is None
        assert ipmi.mac_address is None
        assert ipmi.gateway is None
        assert ipmi.netmask is None
        assert ipmi.vlan_id is None
        assert ipmi.channel is None
        assert ipmi.enabled is False

    def test_ipmi_info_serialization(self):
        """Test IPMIInfo serialization to dict."""
        ipmi = IPMIInfo(ip_address="10.0.0.50", enabled=True)
        data = asdict(ipmi)
        assert data["ip_address"] == "10.0.0.50"
        assert data["enabled"] is True


class TestSystemInfo:
    """Test SystemInfo dataclass."""

    def test_system_info_creation(self):
        """Test creating a SystemInfo instance."""
        system = SystemInfo(
            manufacturer="Dell Inc.",
            product_name="PowerEdge R640",
            serial_number="ABC12345",
            uuid="550e8400-e29b-41d4-a716-446655440000",
            bios_version="2.10.0",
            bios_date="04/12/2023",
            cpu_model="Intel Xeon Gold 6230",
            cpu_cores=40,
            memory_total="128 GB",
            chassis_type="Rack Mount Chassis",
        )
        assert system.manufacturer == "Dell Inc."
        assert system.product_name == "PowerEdge R640"
        assert system.serial_number == "ABC12345"
        assert system.cpu_cores == 40
        assert system.memory_total == "128 GB"

    def test_system_info_defaults(self):
        """Test SystemInfo with default values."""
        system = SystemInfo()
        assert system.manufacturer is None
        assert system.product_name is None
        assert system.serial_number is None
        assert system.uuid is None
        assert system.bios_version is None
        assert system.cpu_cores is None

    def test_system_info_serialization(self):
        """Test SystemInfo serialization to dict."""
        system = SystemInfo(
            manufacturer="HPE",
            product_name="ProLiant DL380",
        )
        data = asdict(system)
        assert data["manufacturer"] == "HPE"
        assert data["product_name"] == "ProLiant DL380"


class TestHardwareDiscovery:
    """Test HardwareDiscovery dataclass."""

    def test_hardware_discovery_creation(self):
        """Test creating a HardwareDiscovery instance."""
        system_info = SystemInfo(manufacturer="Dell Inc.")
        ipmi_info = IPMIInfo(ip_address="192.168.1.50")
        network_interfaces = [
            NetworkInterface(name="eth0", mac_address="00:11:22:33:44:55")
        ]

        discovery = HardwareDiscovery(
            hostname="server01",
            system_info=system_info,
            ipmi_info=ipmi_info,
            network_interfaces=network_interfaces,
            discovered_at="2023-01-01T12:00:00Z",
            discovery_errors=["Warning: Could not detect some hardware"],
        )

        assert discovery.hostname == "server01"
        assert discovery.system_info.manufacturer == "Dell Inc."
        assert discovery.ipmi_info.ip_address == "192.168.1.50"
        assert len(discovery.network_interfaces) == 1
        assert discovery.network_interfaces[0].name == "eth0"
        assert len(discovery.discovery_errors) == 1

    def test_hardware_discovery_to_dict(self):
        """Test HardwareDiscovery to_dict method."""
        system_info = SystemInfo(manufacturer="HPE")
        ipmi_info = IPMIInfo()
        network_interfaces = []

        discovery = HardwareDiscovery(
            hostname="test-server",
            system_info=system_info,
            ipmi_info=ipmi_info,
            network_interfaces=network_interfaces,
            discovered_at="2023-01-01T12:00:00Z",
            discovery_errors=[],
        )

        data = discovery.to_dict()
        assert data["hostname"] == "test-server"
        assert data["system_info"]["manufacturer"] == "HPE"
        assert data["ipmi_info"]["enabled"] is False
        assert data["network_interfaces"] == []
        assert data["discovery_errors"] == []

    def test_hardware_discovery_complex_structure(self):
        """Test HardwareDiscovery with complex nested data."""
        system_info = SystemInfo(
            manufacturer="Supermicro",
            product_name="SYS-2029P-C1R",
            cpu_cores=64,
        )
        ipmi_info = IPMIInfo(
            ip_address="10.0.1.100",
            enabled=True,
            vlan_id=200,
        )
        network_interfaces = [
            NetworkInterface(name="eth0", mac_address="aa:bb:cc:dd:ee:f0"),
            NetworkInterface(name="eth1", mac_address="aa:bb:cc:dd:ee:f1"),
        ]

        discovery = HardwareDiscovery(
            hostname="supermicro-01",
            system_info=system_info,
            ipmi_info=ipmi_info,
            network_interfaces=network_interfaces,
            discovered_at="2023-12-01T10:30:00Z",
            discovery_errors=["IPMI channel 2 not responding"],
        )

        data = discovery.to_dict()
        assert len(data["network_interfaces"]) == 2
        assert data["system_info"]["cpu_cores"] == 64
        assert data["ipmi_info"]["vlan_id"] == 200


class TestBaseVendorDiscovery:
    """Test BaseVendorDiscovery abstract base class."""

    def test_base_vendor_discovery_initialization(self):
        """Test BaseVendorDiscovery initialization."""
        mock_ssh_client = Mock()

        # Create a concrete implementation for testing
        class TestVendorDiscovery(BaseVendorDiscovery):
            def can_handle(self, system_info):
                return True

            def get_vendor_specific_info(self, system_info):
                return {"vendor": "test"}

            def install_vendor_tools(self):
                return True

        discovery = TestVendorDiscovery(mock_ssh_client)
        assert discovery.ssh_client is mock_ssh_client
        assert hasattr(discovery, "logger")

    def test_base_vendor_discovery_default_priority(self):
        """Test BaseVendorDiscovery default priority."""
        mock_ssh_client = Mock()

        class TestVendorDiscovery(BaseVendorDiscovery):
            def can_handle(self, system_info):
                return True

            def get_vendor_specific_info(self, system_info):
                return {}

            def install_vendor_tools(self):
                return True

        discovery = TestVendorDiscovery(mock_ssh_client)
        assert discovery.get_priority() == 100

    def test_base_vendor_discovery_abstract_methods(self):
        """Test that BaseVendorDiscovery abstract methods must be implemented."""
        mock_ssh_client = Mock()

        # This should raise TypeError because abstract methods aren't implemented
        with pytest.raises(TypeError):
            BaseVendorDiscovery(mock_ssh_client)

    def test_concrete_vendor_discovery_implementation(self):
        """Test a concrete implementation of BaseVendorDiscovery."""
        mock_ssh_client = Mock()

        class DellVendorDiscovery(BaseVendorDiscovery):
            def can_handle(self, system_info):
                return system_info.manufacturer == "Dell Inc."

            def get_vendor_specific_info(self, system_info):
                return {"vendor": "Dell", "tools": ["racadm"]}

            def install_vendor_tools(self):
                return True

            def get_priority(self):
                return 10  # Higher priority than default

        discovery = DellVendorDiscovery(mock_ssh_client)
        system_info = SystemInfo(manufacturer="Dell Inc.")

        assert discovery.can_handle(system_info) is True
        vendor_info = discovery.get_vendor_specific_info(system_info)
        assert vendor_info["vendor"] == "Dell"
        assert discovery.install_vendor_tools() is True
        assert discovery.get_priority() == 10


class TestBaseParser:
    """Test BaseParser abstract base class."""

    def test_base_parser_initialization(self):
        """Test BaseParser initialization."""

        # Create a concrete implementation for testing
        class TestParser(BaseParser):
            def parse(self, output):
                return {"parsed": True}

        parser = TestParser()
        assert hasattr(parser, "logger")

    def test_base_parser_abstract_method(self):
        """Test that BaseParser abstract method must be implemented."""
        # This should raise TypeError because parse method isn't implemented
        with pytest.raises(TypeError):
            BaseParser()

    def test_concrete_parser_implementation(self):
        """Test a concrete implementation of BaseParser."""

        class JSONParser(BaseParser):
            def parse(self, output):
                import json

                return json.loads(output) if output.strip() else {}

        parser = JSONParser()
        result = parser.parse('{"test": "value"}')
        assert result["test"] == "value"

    def test_safe_parse_success(self):
        """Test BaseParser safe_parse with successful parsing."""

        class TestParser(BaseParser):
            def parse(self, output):
                return {"lines": len(output.split("\n"))}

        parser = TestParser()
        result = parser.safe_parse("line1\nline2\nline3")
        assert result["lines"] == 3

    def test_safe_parse_error_handling(self):
        """Test BaseParser safe_parse with parsing error."""

        class FailingParser(BaseParser):
            def parse(self, output):
                raise ValueError("Parse error")

        parser = FailingParser()
        result = parser.safe_parse("any input")
        assert result == {}  # Should return empty dict on error

    @patch("hwautomation.hardware.discovery.base.get_logger")
    def test_safe_parse_logs_warning(self, mock_get_logger):
        """Test that safe_parse logs warnings on parsing errors."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        class FailingParser(BaseParser):
            def parse(self, output):
                raise ValueError("Parse failed")

        parser = FailingParser()
        parser.safe_parse("test input")

        # Verify logger.warning was called
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args[0][0]
        assert "Failed to parse output" in call_args
