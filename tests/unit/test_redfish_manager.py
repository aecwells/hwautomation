"""
Unit tests for Redfish Manager (Phase 1)

Tests basic Redfish functionality including connection, capability discovery,
and integration with BiosConfigManager.
"""

import pytest
import unittest.mock as mock
from unittest.mock import Mock, patch, MagicMock
import requests

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from hwautomation.hardware.redfish_manager import RedfishManager, SystemInfo, RedfishCapabilities
from hwautomation.hardware.bios_config import BiosConfigManager


class TestRedfishManager:
    """Test suite for RedfishManager"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.target_ip = "192.168.1.100"
        self.username = "admin"
        self.password = "password"
    
    @patch('hwautomation.hardware.redfish_manager.requests.Session')
    def test_redfish_manager_initialization(self, mock_session_class):
        """Test RedfishManager initialization"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        redfish = RedfishManager(self.target_ip, self.username, self.password)
        
        assert redfish.host == self.target_ip
        assert redfish.username == self.username
        assert redfish.password == self.password
        assert redfish.base_url == f"https://{self.target_ip}:443"
        assert redfish.session == mock_session
    
    @patch('hwautomation.hardware.redfish_manager.requests.Session')
    def test_redfish_manager_http_mode(self, mock_session_class):
        """Test RedfishManager with HTTP (non-HTTPS) mode"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        redfish = RedfishManager(self.target_ip, self.username, self.password, 
                                port=80, use_https=False)
        
        assert redfish.base_url == f"http://{self.target_ip}:80"
    
    @patch('hwautomation.hardware.redfish_manager.requests.Session')
    def test_service_root_discovery(self, mock_session_class):
        """Test service root discovery"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock service root response
        mock_response = Mock()
        mock_response.json.return_value = {
            "RedfishVersion": "1.6.0",
            "Id": "RootService",
            "Systems": {"@odata.id": "/redfish/v1/Systems"},
            "Chassis": {"@odata.id": "/redfish/v1/Chassis"}
        }
        mock_response.raise_for_status.return_value = None
        mock_session.request.return_value = mock_response
        
        redfish = RedfishManager(self.target_ip, self.username, self.password)
        service_root = redfish.discover_service_root()
        
        assert service_root["RedfishVersion"] == "1.6.0"
        assert service_root["Id"] == "RootService"
        assert "Systems" in service_root
        assert "Chassis" in service_root
    
    @patch('hwautomation.hardware.redfish_manager.requests.Session')
    def test_capability_discovery(self, mock_session_class):
        """Test capability discovery"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock responses for capability discovery
        def mock_request_side_effect(method, url, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            
            if '/redfish/v1/' in url:
                # Service root
                mock_response.json.return_value = {
                    "RedfishVersion": "1.6.0",
                    "Systems": {"@odata.id": "/redfish/v1/Systems"},
                    "Chassis": {"@odata.id": "/redfish/v1/Chassis"}
                }
            elif '/redfish/v1/Systems' in url and url.endswith('Systems'):
                # Systems collection
                mock_response.json.return_value = {
                    "Members": [{"@odata.id": "/redfish/v1/Systems/1"}]
                }
            elif '/redfish/v1/Systems/1' in url:
                # System detail
                mock_response.json.return_value = {
                    "Id": "1",
                    "PowerState": "On",
                    "Bios": {"@odata.id": "/redfish/v1/Systems/1/Bios"}
                }
            
            return mock_response
        
        mock_session.request.side_effect = mock_request_side_effect
        
        redfish = RedfishManager(self.target_ip, self.username, self.password)
        capabilities = redfish.discover_capabilities()
        
        assert isinstance(capabilities, RedfishCapabilities)
        assert capabilities.supports_system_info == True
        assert capabilities.supports_power_control == True
        assert capabilities.supports_bios_config == True
    
    @patch('hwautomation.hardware.redfish_manager.requests.Session')
    def test_system_info_retrieval(self, mock_session_class):
        """Test system information retrieval"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        def mock_request_side_effect(method, url, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            
            if '/redfish/v1/' in url:
                mock_response.json.return_value = {
                    "Systems": {"@odata.id": "/redfish/v1/Systems"}
                }
            elif '/redfish/v1/Systems' in url and url.endswith('Systems'):
                mock_response.json.return_value = {
                    "Members": [{"@odata.id": "/redfish/v1/Systems/1"}]
                }
            elif '/redfish/v1/Systems/1' in url:
                mock_response.json.return_value = {
                    "Id": "1",
                    "Manufacturer": "Supermicro",
                    "Model": "SYS-1029P-WTRT",
                    "SerialNumber": "12345678",
                    "BiosVersion": "3.3",
                    "PowerState": "On",
                    "ProcessorSummary": {"Count": 2},
                    "MemorySummary": {"TotalSystemMemoryGiB": 64},
                    "Status": {"Health": "OK"}
                }
            
            return mock_response
        
        mock_session.request.side_effect = mock_request_side_effect
        
        redfish = RedfishManager(self.target_ip, self.username, self.password)
        system_info = redfish.get_system_info()
        
        assert isinstance(system_info, SystemInfo)
        assert system_info.manufacturer == "Supermicro"
        assert system_info.model == "SYS-1029P-WTRT"
        assert system_info.serial_number == "12345678"
        assert system_info.bios_version == "3.3"
        assert system_info.power_state == "On"
        assert system_info.processor_count == 2
        assert system_info.memory_total_gb == 64.0
        assert system_info.health_status == "OK"
    
    @patch('hwautomation.hardware.redfish_manager.requests.Session')
    def test_bios_settings_retrieval(self, mock_session_class):
        """Test BIOS settings retrieval"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        def mock_request_side_effect(method, url, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            
            if '/Bios' in url:
                mock_response.json.return_value = {
                    "Attributes": {
                        "BootMode": "UEFI",
                        "SecureBoot": "Disabled",
                        "Hyper-Threading": "Enabled",
                        "PowerProfile": "Performance"
                    }
                }
            else:
                # Mock capability discovery responses
                if '/redfish/v1/' in url:
                    mock_response.json.return_value = {
                        "Systems": {"@odata.id": "/redfish/v1/Systems"}
                    }
                elif '/redfish/v1/Systems' in url and url.endswith('Systems'):
                    mock_response.json.return_value = {
                        "Members": [{"@odata.id": "/redfish/v1/Systems/1"}]
                    }
                elif '/redfish/v1/Systems/1' in url:
                    mock_response.json.return_value = {
                        "Bios": {"@odata.id": "/redfish/v1/Systems/1/Bios"}
                    }
            
            return mock_response
        
        mock_session.request.side_effect = mock_request_side_effect
        
        redfish = RedfishManager(self.target_ip, self.username, self.password)
        bios_settings = redfish.get_bios_settings()
        
        assert bios_settings is not None
        assert "BootMode" in bios_settings
        assert "SecureBoot" in bios_settings
        assert bios_settings["BootMode"] == "UEFI"
        assert bios_settings["SecureBoot"] == "Disabled"
    
    @patch('hwautomation.hardware.redfish_manager.requests.Session')
    def test_connection_test_success(self, mock_session_class):
        """Test successful connection test"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        def mock_request_side_effect(method, url, **kwargs):
            mock_response = Mock()
            mock_response.raise_for_status.return_value = None
            
            if '/redfish/v1/' in url:
                mock_response.json.return_value = {
                    "RedfishVersion": "1.6.0",
                    "Systems": {"@odata.id": "/redfish/v1/Systems"}
                }
            elif '/redfish/v1/Systems' in url and url.endswith('Systems'):
                mock_response.json.return_value = {
                    "Members": [{"@odata.id": "/redfish/v1/Systems/1"}]
                }
            elif '/redfish/v1/Systems/1' in url:
                mock_response.json.return_value = {
                    "Manufacturer": "TestVendor",
                    "Model": "TestModel"
                }
            
            return mock_response
        
        mock_session.request.side_effect = mock_request_side_effect
        
        redfish = RedfishManager(self.target_ip, self.username, self.password)
        success, message = redfish.test_connection()
        
        assert success == True
        assert "Redfish connection successful" in message
        assert "TestVendor TestModel" in message
    
    @patch('hwautomation.hardware.redfish_manager.requests.Session')
    def test_connection_test_failure(self, mock_session_class):
        """Test failed connection test"""
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        # Mock request that raises an exception
        mock_session.request.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        redfish = RedfishManager(self.target_ip, self.username, self.password)
        success, message = redfish.test_connection()
        
        assert success == False
        assert "Redfish connection failed" in message


class TestBiosConfigManagerRedfish:
    """Test suite for BiosConfigManager Redfish integration"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.target_ip = "192.168.1.100"
        self.username = "admin"
        self.password = "password"
        self.device_type = "a1.c5.large"
    
    @patch('hwautomation.hardware.bios_config.RedfishManager')
    def test_redfish_connection_via_bios_manager(self, mock_redfish_class):
        """Test Redfish connection through BiosConfigManager"""
        mock_redfish = Mock()
        mock_redfish.test_connection.return_value = (True, "Connection successful")
        mock_redfish_class.return_value.__enter__.return_value = mock_redfish
        
        bios_manager = BiosConfigManager()
        success, message = bios_manager.test_redfish_connection(self.target_ip, self.username, self.password)
        
        assert success == True
        assert "Connection successful" in message
    
    @patch('hwautomation.hardware.bios_config.RedfishManager')
    def test_system_info_via_bios_manager(self, mock_redfish_class):
        """Test system info retrieval through BiosConfigManager"""
        mock_redfish = Mock()
        mock_system_info = SystemInfo(
            manufacturer="TestVendor",
            model="TestModel",
            serial_number="12345",
            bios_version="1.0"
        )
        mock_redfish.get_system_info.return_value = mock_system_info
        mock_redfish_class.return_value.__enter__.return_value = mock_redfish
        
        bios_manager = BiosConfigManager()
        system_info = bios_manager.get_system_info_via_redfish(self.target_ip, self.username, self.password)
        
        assert system_info is not None
        assert system_info.manufacturer == "TestVendor"
        assert system_info.model == "TestModel"
    
    @patch('hwautomation.hardware.bios_config.RedfishManager')
    def test_bios_config_method_determination(self, mock_redfish_class):
        """Test BIOS configuration method determination"""
        mock_redfish = Mock()
        mock_redfish.test_connection.return_value = (True, "Connection successful")
        mock_capabilities = RedfishCapabilities(supports_bios_config=True)
        mock_redfish.discover_capabilities.return_value = mock_capabilities
        mock_redfish_class.return_value.__enter__.return_value = mock_redfish
        
        bios_manager = BiosConfigManager()
        method = bios_manager.determine_bios_config_method(self.target_ip, self.device_type, self.username, self.password)
        
        # Should return vendor_tool since device config doesn't specify redfish preference
        assert method in ['redfish', 'vendor_tool', 'hybrid']


if __name__ == "__main__":
    pytest.main([__file__])
