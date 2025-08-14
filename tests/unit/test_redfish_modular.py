"""
Comprehensive test suite for the modular Redfish components in hwautomation.hardware.redfish.managers.

This module tests all the newly refactored Redfish manager components:
- RedfishCoordinator: Main coordination of all Redfish operations
- PowerManager: Power management operations
- BiosManager: BIOS configuration management
- SystemManager: System information and hardware details
- FirmwareManager: Firmware management operations
- BaseManager: Common base functionality
"""

import json
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, Mock, patch

import pytest

from hwautomation.hardware.redfish.managers import (
    BaseRedfishManager,
    RedfishBiosManager,
    RedfishCoordinator,
    RedfishFirmwareManager,
    RedfishPowerManager,
    RedfishSystemManager,
)


class TestBaseManager:
    """Test suite for BaseManager common functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.base_manager = BaseManager(self.mock_client)

    def test_base_manager_initialization(self):
        """Test BaseManager initializes properly."""
        assert self.base_manager.client == self.mock_client
        assert hasattr(self.base_manager, "logger")

    def test_make_request_success(self):
        """Test successful request through base manager."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "success"}

        self.mock_client.get.return_value = mock_response

        result = self.base_manager._make_request("GET", "/test/endpoint")

        assert result == {"result": "success"}
        self.mock_client.get.assert_called_once_with("/test/endpoint")

    def test_make_request_http_error(self):
        """Test request with HTTP error."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"

        self.mock_client.get.return_value = mock_response

        with pytest.raises(Exception, match="HTTP 404"):
            self.base_manager._make_request("GET", "/nonexistent")

    def test_make_request_with_data(self):
        """Test request with data payload."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"created": True}

        self.mock_client.post.return_value = mock_response

        data = {"key": "value"}
        result = self.base_manager._make_request("POST", "/create", data=data)

        assert result == {"created": True}
        self.mock_client.post.assert_called_once_with("/create", json=data)

    def test_validate_response_structure(self):
        """Test response structure validation."""
        # Valid response
        valid_response = {"@odata.type": "#Resource.v1_0_0.Resource", "Id": "test"}
        assert self.base_manager._validate_response(valid_response) is True

        # Invalid response (missing required fields)
        invalid_response = {"random": "data"}
        assert self.base_manager._validate_response(invalid_response) is False

    def test_error_handling_utility(self):
        """Test error handling utilities."""
        error_response = {
            "error": {
                "@Message.ExtendedInfo": [
                    {"Message": "Test error message", "Severity": "Critical"}
                ]
            }
        }

        error_msg = self.base_manager._extract_error_message(error_response)
        assert "Test error message" in error_msg

    def test_format_operation_result(self):
        """Test operation result formatting."""
        result = self.base_manager._format_result(
            success=True, message="Operation completed", data={"key": "value"}
        )

        assert result["success"] is True
        assert result["message"] == "Operation completed"
        assert result["data"] == {"key": "value"}
        assert "timestamp" in result


class TestPowerManager:
    """Test suite for PowerManager power operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.power_manager = PowerManager(self.mock_client)

    def test_power_manager_initialization(self):
        """Test PowerManager initializes properly."""
        assert isinstance(self.power_manager, BaseManager)
        assert self.power_manager.client == self.mock_client

    def test_get_power_state(self):
        """Test getting current power state."""
        mock_response = {
            "PowerState": "On",
            "@odata.type": "#ComputerSystem.v1_0_0.ComputerSystem",
        }

        with patch.object(
            self.power_manager, "_make_request", return_value=mock_response
        ):
            state = self.power_manager.get_power_state()

        assert state == "On"

    def test_get_power_state_invalid_response(self):
        """Test getting power state with invalid response."""
        mock_response = {"invalid": "response"}

        with patch.object(
            self.power_manager, "_make_request", return_value=mock_response
        ):
            state = self.power_manager.get_power_state()

        assert state is None

    def test_power_on_operation(self):
        """Test power on operation."""
        mock_task_response = {"TaskState": "Completed", "TaskStatus": "OK"}

        with patch.object(
            self.power_manager, "_make_request", return_value=mock_task_response
        ):
            result = self.power_manager.power_on()

        assert result["success"] is True
        assert "powered on" in result["message"].lower()

    def test_power_off_operation(self):
        """Test power off operation."""
        mock_task_response = {"TaskState": "Completed", "TaskStatus": "OK"}

        with patch.object(
            self.power_manager, "_make_request", return_value=mock_task_response
        ):
            result = self.power_manager.power_off()

        assert result["success"] is True
        assert "powered off" in result["message"].lower()

    def test_power_cycle_operation(self):
        """Test power cycle operation."""
        mock_task_response = {"TaskState": "Completed", "TaskStatus": "OK"}

        with patch.object(
            self.power_manager, "_make_request", return_value=mock_task_response
        ):
            result = self.power_manager.power_cycle()

        assert result["success"] is True
        assert "power cycle" in result["message"].lower()

    def test_graceful_shutdown_operation(self):
        """Test graceful shutdown operation."""
        mock_task_response = {"TaskState": "Completed", "TaskStatus": "OK"}

        with patch.object(
            self.power_manager, "_make_request", return_value=mock_task_response
        ):
            result = self.power_manager.graceful_shutdown()

        assert result["success"] is True
        assert "graceful shutdown" in result["message"].lower()

    def test_force_restart_operation(self):
        """Test force restart operation."""
        mock_task_response = {"TaskState": "Completed", "TaskStatus": "OK"}

        with patch.object(
            self.power_manager, "_make_request", return_value=mock_task_response
        ):
            result = self.power_manager.force_restart()

        assert result["success"] is True
        assert "force restart" in result["message"].lower()

    def test_power_operation_failure(self):
        """Test power operation failure handling."""
        with patch.object(
            self.power_manager,
            "_make_request",
            side_effect=Exception("Power operation failed"),
        ):
            result = self.power_manager.power_on()

        assert result["success"] is False
        assert "Power operation failed" in result["error"]

    def test_get_supported_power_actions(self):
        """Test getting supported power actions."""
        mock_response = {
            "Actions": {
                "#ComputerSystem.Reset": {
                    "ResetType@Redfish.AllowableValues": [
                        "On",
                        "ForceOff",
                        "GracefulShutdown",
                        "ForceRestart",
                        "Nmi",
                        "PowerCycle",
                    ]
                }
            }
        }

        with patch.object(
            self.power_manager, "_make_request", return_value=mock_response
        ):
            actions = self.power_manager.get_supported_actions()

        assert "On" in actions
        assert "PowerCycle" in actions
        assert len(actions) == 6


class TestBiosManager:
    """Test suite for BiosManager BIOS configuration operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.bios_manager = BiosManager(self.mock_client)

    def test_bios_manager_initialization(self):
        """Test BiosManager initializes properly."""
        assert isinstance(self.bios_manager, BaseManager)
        assert self.bios_manager.client == self.mock_client

    def test_get_bios_settings(self):
        """Test getting BIOS settings."""
        mock_response = {
            "Attributes": {
                "BootMode": "Uefi",
                "SecureBoot": "Enabled",
                "VirtualizationTechnology": "Enabled",
            },
            "@odata.type": "#Bios.v1_0_0.Bios",
        }

        with patch.object(
            self.bios_manager, "_make_request", return_value=mock_response
        ):
            settings = self.bios_manager.get_bios_settings()

        assert settings["BootMode"] == "Uefi"
        assert settings["SecureBoot"] == "Enabled"
        assert settings["VirtualizationTechnology"] == "Enabled"

    def test_get_specific_bios_setting(self):
        """Test getting a specific BIOS setting."""
        mock_response = {"Attributes": {"BootMode": "Uefi", "SecureBoot": "Enabled"}}

        with patch.object(
            self.bios_manager, "_make_request", return_value=mock_response
        ):
            boot_mode = self.bios_manager.get_bios_setting("BootMode")

        assert boot_mode == "Uefi"

    def test_get_nonexistent_bios_setting(self):
        """Test getting a non-existent BIOS setting."""
        mock_response = {"Attributes": {"BootMode": "Uefi"}}

        with patch.object(
            self.bios_manager, "_make_request", return_value=mock_response
        ):
            setting = self.bios_manager.get_bios_setting("NonExistentSetting")

        assert setting is None

    def test_set_bios_settings(self):
        """Test setting BIOS configuration."""
        new_settings = {"BootMode": "Legacy", "SecureBoot": "Disabled"}

        mock_task_response = {"TaskState": "Completed", "TaskStatus": "OK"}

        with patch.object(
            self.bios_manager, "_make_request", return_value=mock_task_response
        ):
            result = self.bios_manager.set_bios_settings(new_settings)

        assert result["success"] is True
        assert "BIOS settings updated" in result["message"]

    def test_set_single_bios_setting(self):
        """Test setting a single BIOS setting."""
        mock_task_response = {"TaskState": "Completed", "TaskStatus": "OK"}

        with patch.object(
            self.bios_manager, "_make_request", return_value=mock_task_response
        ):
            result = self.bios_manager.set_bios_setting("BootMode", "Uefi")

        assert result["success"] is True
        assert "BootMode" in result["message"]

    def test_reset_bios_to_defaults(self):
        """Test resetting BIOS to defaults."""
        mock_task_response = {"TaskState": "Completed", "TaskStatus": "OK"}

        with patch.object(
            self.bios_manager, "_make_request", return_value=mock_task_response
        ):
            result = self.bios_manager.reset_to_defaults()

        assert result["success"] is True
        assert "reset to defaults" in result["message"].lower()

    def test_get_bios_attribute_registry(self):
        """Test getting BIOS attribute registry."""
        mock_response = {
            "RegistryEntries": {
                "Attributes": [
                    {
                        "AttributeName": "BootMode",
                        "Type": "Enumeration",
                        "Value": [{"ValueName": "Uefi"}, {"ValueName": "Legacy"}],
                    }
                ]
            }
        }

        with patch.object(
            self.bios_manager, "_make_request", return_value=mock_response
        ):
            registry = self.bios_manager.get_attribute_registry()

        assert "Attributes" in registry["RegistryEntries"]
        assert len(registry["RegistryEntries"]["Attributes"]) == 1

    def test_validate_bios_setting_value(self):
        """Test BIOS setting value validation."""
        mock_registry = {
            "RegistryEntries": {
                "Attributes": [
                    {
                        "AttributeName": "BootMode",
                        "Type": "Enumeration",
                        "Value": [{"ValueName": "Uefi"}, {"ValueName": "Legacy"}],
                    }
                ]
            }
        }

        with patch.object(
            self.bios_manager, "get_attribute_registry", return_value=mock_registry
        ):
            # Valid value
            is_valid = self.bios_manager.validate_setting_value("BootMode", "Uefi")
            assert is_valid is True

            # Invalid value
            is_valid = self.bios_manager.validate_setting_value(
                "BootMode", "InvalidMode"
            )
            assert is_valid is False


class TestSystemManager:
    """Test suite for SystemManager system information operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.system_manager = SystemManager(self.mock_client)

    def test_system_manager_initialization(self):
        """Test SystemManager initializes properly."""
        assert isinstance(self.system_manager, BaseManager)
        assert self.system_manager.client == self.mock_client

    def test_get_system_info(self):
        """Test getting system information."""
        mock_response = {
            "Manufacturer": "Dell Inc.",
            "Model": "PowerEdge R740",
            "SerialNumber": "ABC123",
            "BiosVersion": "2.8.1",
            "ProcessorSummary": {"Count": 2, "Model": "Intel Xeon Gold 6230"},
            "MemorySummary": {"TotalSystemMemoryGiB": 256},
        }

        with patch.object(
            self.system_manager, "_make_request", return_value=mock_response
        ):
            info = self.system_manager.get_system_info()

        assert info["Manufacturer"] == "Dell Inc."
        assert info["Model"] == "PowerEdge R740"
        assert info["ProcessorSummary"]["Count"] == 2
        assert info["MemorySummary"]["TotalSystemMemoryGiB"] == 256

    def test_get_hardware_inventory(self):
        """Test getting hardware inventory."""
        mock_processors = {
            "Members": [
                {"@odata.id": "/redfish/v1/Systems/1/Processors/CPU1"},
                {"@odata.id": "/redfish/v1/Systems/1/Processors/CPU2"},
            ]
        }

        mock_memory = {
            "Members": [
                {"@odata.id": "/redfish/v1/Systems/1/Memory/DIMM1"},
                {"@odata.id": "/redfish/v1/Systems/1/Memory/DIMM2"},
            ]
        }

        with patch.object(self.system_manager, "_make_request") as mock_request:
            mock_request.side_effect = [mock_processors, mock_memory]

            inventory = self.system_manager.get_hardware_inventory()

        assert len(inventory["processors"]) == 2
        assert len(inventory["memory"]) == 2

    def test_get_thermal_status(self):
        """Test getting thermal status."""
        mock_response = {
            "Temperatures": [
                {
                    "Name": "CPU1 Temperature",
                    "ReadingCelsius": 45,
                    "Status": {"State": "Enabled", "Health": "OK"},
                },
                {
                    "Name": "CPU2 Temperature",
                    "ReadingCelsius": 47,
                    "Status": {"State": "Enabled", "Health": "OK"},
                },
            ],
            "Fans": [
                {
                    "Name": "System Fan 1",
                    "Reading": 3500,
                    "Status": {"State": "Enabled", "Health": "OK"},
                }
            ],
        }

        with patch.object(
            self.system_manager, "_make_request", return_value=mock_response
        ):
            thermal = self.system_manager.get_thermal_status()

        assert len(thermal["Temperatures"]) == 2
        assert len(thermal["Fans"]) == 1
        assert thermal["Temperatures"][0]["ReadingCelsius"] == 45

    def test_get_power_consumption(self):
        """Test getting power consumption data."""
        mock_response = {
            "PowerConsumedWatts": 250,
            "PowerMetrics": {
                "AverageConsumedWatts": 225,
                "MaxConsumedWatts": 300,
                "MinConsumedWatts": 180,
            },
        }

        with patch.object(
            self.system_manager, "_make_request", return_value=mock_response
        ):
            power = self.system_manager.get_power_consumption()

        assert power["PowerConsumedWatts"] == 250
        assert power["PowerMetrics"]["AverageConsumedWatts"] == 225

    def test_get_network_interfaces(self):
        """Test getting network interface information."""
        mock_response = {
            "Members": [
                {
                    "@odata.id": "/redfish/v1/Systems/1/EthernetInterfaces/NIC1",
                    "MACAddress": "AA:BB:CC:DD:EE:FF",
                    "LinkStatus": "LinkUp",
                    "SpeedMbps": 1000,
                },
                {
                    "@odata.id": "/redfish/v1/Systems/1/EthernetInterfaces/NIC2",
                    "MACAddress": "11:22:33:44:55:66",
                    "LinkStatus": "LinkDown",
                    "SpeedMbps": None,
                },
            ]
        }

        with patch.object(
            self.system_manager, "_make_request", return_value=mock_response
        ):
            interfaces = self.system_manager.get_network_interfaces()

        assert len(interfaces["Members"]) == 2
        assert interfaces["Members"][0]["LinkStatus"] == "LinkUp"
        assert interfaces["Members"][1]["LinkStatus"] == "LinkDown"


class TestFirmwareManager:
    """Test suite for FirmwareManager firmware operations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.firmware_manager = FirmwareManager(self.mock_client)

    def test_firmware_manager_initialization(self):
        """Test FirmwareManager initializes properly."""
        assert isinstance(self.firmware_manager, BaseManager)
        assert self.firmware_manager.client == self.mock_client

    def test_get_firmware_inventory(self):
        """Test getting firmware inventory."""
        mock_response = {
            "Members": [
                {
                    "Name": "BIOS",
                    "Version": "2.8.1",
                    "Status": {"State": "Enabled", "Health": "OK"},
                    "Updateable": True,
                },
                {
                    "Name": "BMC Firmware",
                    "Version": "4.40.00.00",
                    "Status": {"State": "Enabled", "Health": "OK"},
                    "Updateable": True,
                },
            ]
        }

        with patch.object(
            self.firmware_manager, "_make_request", return_value=mock_response
        ):
            inventory = self.firmware_manager.get_firmware_inventory()

        assert len(inventory["Members"]) == 2
        assert inventory["Members"][0]["Name"] == "BIOS"
        assert inventory["Members"][1]["Version"] == "4.40.00.00"

    def test_get_updateable_firmware(self):
        """Test getting updateable firmware components."""
        mock_response = {
            "Members": [
                {"Name": "BIOS", "Version": "2.8.1", "Updateable": True},
                {"Name": "BMC Firmware", "Version": "4.40.00.00", "Updateable": True},
                {"Name": "NIC Firmware", "Version": "1.2.3", "Updateable": False},
            ]
        }

        with patch.object(
            self.firmware_manager, "_make_request", return_value=mock_response
        ):
            updateable = self.firmware_manager.get_updateable_firmware()

        assert len(updateable) == 2
        assert all(fw["Updateable"] for fw in updateable)

    def test_initiate_firmware_update(self):
        """Test initiating firmware update."""
        mock_task_response = {
            "@odata.id": "/redfish/v1/TaskService/Tasks/123",
            "TaskState": "Running",
            "TaskStatus": "OK",
        }

        with patch.object(
            self.firmware_manager, "_make_request", return_value=mock_task_response
        ):
            result = self.firmware_manager.initiate_firmware_update(
                image_uri="https://example.com/firmware.bin", targets=["BIOS"]
            )

        assert result["success"] is True
        assert "update initiated" in result["message"].lower()
        assert "task_id" in result

    def test_check_update_status(self):
        """Test checking firmware update status."""
        mock_task_response = {
            "TaskState": "Running",
            "TaskStatus": "OK",
            "PercentComplete": 45,
            "Messages": [{"Message": "Firmware update in progress"}],
        }

        with patch.object(
            self.firmware_manager, "_make_request", return_value=mock_task_response
        ):
            status = self.firmware_manager.check_update_status("task-123")

        assert status["TaskState"] == "Running"
        assert status["PercentComplete"] == 45

    def test_cancel_firmware_update(self):
        """Test canceling firmware update."""
        mock_response = {"TaskState": "Cancelled", "TaskStatus": "OK"}

        with patch.object(
            self.firmware_manager, "_make_request", return_value=mock_response
        ):
            result = self.firmware_manager.cancel_firmware_update("task-123")

        assert result["success"] is True
        assert "cancelled" in result["message"].lower()


class TestRedfishCoordinator:
    """Test suite for RedfishCoordinator main coordination functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.coordinator = RedfishCoordinator("test.example.com", "admin", "password")

    def test_redfish_coordinator_initialization(self):
        """Test RedfishCoordinator initializes properly."""
        assert self.coordinator.host == "test.example.com"
        assert self.coordinator.username == "admin"
        assert hasattr(self.coordinator, "power_manager")
        assert hasattr(self.coordinator, "bios_manager")
        assert hasattr(self.coordinator, "system_manager")
        assert hasattr(self.coordinator, "firmware_manager")

    def test_coordinator_manager_types(self):
        """Test that coordinator creates proper manager types."""
        assert isinstance(self.coordinator.power_manager, PowerManager)
        assert isinstance(self.coordinator.bios_manager, BiosManager)
        assert isinstance(self.coordinator.system_manager, SystemManager)
        assert isinstance(self.coordinator.firmware_manager, FirmwareManager)

    def test_coordinator_power_operations(self):
        """Test power operations through coordinator."""
        with patch.object(self.coordinator.power_manager, "power_on") as mock_power_on:
            mock_power_on.return_value = {"success": True, "message": "Powered on"}

            result = self.coordinator.power_on()

        assert result["success"] is True
        mock_power_on.assert_called_once()

    def test_coordinator_bios_operations(self):
        """Test BIOS operations through coordinator."""
        with patch.object(
            self.coordinator.bios_manager, "get_bios_settings"
        ) as mock_get_bios:
            mock_get_bios.return_value = {"BootMode": "Uefi"}

            settings = self.coordinator.get_bios_settings()

        assert settings["BootMode"] == "Uefi"
        mock_get_bios.assert_called_once()

    def test_coordinator_system_operations(self):
        """Test system operations through coordinator."""
        with patch.object(
            self.coordinator.system_manager, "get_system_info"
        ) as mock_get_info:
            mock_get_info.return_value = {"Manufacturer": "Dell Inc."}

            info = self.coordinator.get_system_info()

        assert info["Manufacturer"] == "Dell Inc."
        mock_get_info.assert_called_once()

    def test_coordinator_firmware_operations(self):
        """Test firmware operations through coordinator."""
        with patch.object(
            self.coordinator.firmware_manager, "get_firmware_inventory"
        ) as mock_get_fw:
            mock_get_fw.return_value = {"Members": [{"Name": "BIOS"}]}

            inventory = self.coordinator.get_firmware_inventory()

        assert len(inventory["Members"]) == 1
        mock_get_fw.assert_called_once()

    def test_coordinator_operation_delegation(self):
        """Test that coordinator properly delegates operations."""
        # Test that all managers are accessible and operations are delegated
        operations = [
            ("power_on", "power_manager"),
            ("get_bios_settings", "bios_manager"),
            ("get_system_info", "system_manager"),
            ("get_firmware_inventory", "firmware_manager"),
        ]

        for operation_name, manager_name in operations:
            assert hasattr(self.coordinator, operation_name)
            manager = getattr(self.coordinator, manager_name)
            assert hasattr(
                manager, operation_name.replace("get_", "").replace("_", "_")
            )

    def test_coordinator_health_check(self):
        """Test coordinator health check functionality."""
        with patch.object(
            self.coordinator.system_manager, "get_system_info"
        ) as mock_get_info:
            mock_get_info.return_value = {
                "Status": {"State": "Enabled", "Health": "OK"}
            }

            health = self.coordinator.health_check()

        assert health["success"] is True
        assert health["status"]["Health"] == "OK"

    def test_coordinator_error_handling(self):
        """Test coordinator error handling."""
        with patch.object(self.coordinator.power_manager, "power_on") as mock_power_on:
            mock_power_on.side_effect = Exception("Connection failed")

            result = self.coordinator.power_on()

        assert result["success"] is False
        assert "Connection failed" in result["error"]


class TestBackwardCompatibility:
    """Test suite for backward compatibility of refactored Redfish components."""

    def test_redfish_manager_import_compatibility(self):
        """Test that old RedfishManager import still works."""
        # This should work without modification
        from hwautomation.hardware.redfish.manager import RedfishManager
        from hwautomation.hardware.redfish.managers import RedfishCoordinator

        # Should be aliased to the same class
        assert RedfishManager is RedfishCoordinator

    def test_redfish_manager_api_compatibility(self):
        """Test that old API still works with new implementation."""
        # Test old import path
        from hwautomation.hardware.redfish.manager import RedfishManager

        manager = RedfishManager("test.example.com", "admin", "password")

        # All old methods should still be available
        assert hasattr(manager, "power_on")
        assert hasattr(manager, "get_bios_settings")
        assert hasattr(manager, "get_system_info")
        assert hasattr(manager, "get_firmware_inventory")

    def test_redfish_manager_functionality_compatibility(self):
        """Test that old functionality still works identically."""
        from hwautomation.hardware.redfish.manager import RedfishManager

        old_manager = RedfishManager("test.example.com", "admin", "password")

        # Test that it has the same interface as the new coordinator
        assert hasattr(old_manager, "power_manager")
        assert hasattr(old_manager, "bios_manager")
        assert hasattr(old_manager, "system_manager")
        assert hasattr(old_manager, "firmware_manager")


if __name__ == "__main__":
    pytest.main([__file__])
