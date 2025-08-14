"""
Phase 6 Focused Test Suite: MAAS Client Operations Coverage
========================================================

Targeting MAAS client operations with comprehensive test coverage for:
- MaasClient initialization and OAuth authentication
- Machine management operations (get, commission, deploy, release)
- Status and filtering operations
- IP address extraction and network operations
- Summary and detailed machine information
- Error handling and API response processing

Current Coverage: client.py (17%)
Target: Achieve 50%+ coverage on MAAS client operations
"""

import json
import unittest
from typing import Any, Dict, List
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests
from requests_oauthlib import OAuth1Session

from src.hwautomation.maas.client import MaasClient


class TestMaasClientInitialization(unittest.TestCase):
    """Test MaasClient initialization and setup."""

    def test_init_basic(self):
        """Test basic MaasClient initialization."""
        host = "http://maas.example.com:5240/MAAS"
        consumer_key = "test_key"
        consumer_token = "test_token"
        secret = "test_secret"

        client = MaasClient(host, consumer_key, consumer_token, secret)

        # Verify initialization
        self.assertEqual(client.host, "http://maas.example.com:5240/MAAS")
        self.assertEqual(client.consumer_key, consumer_key)
        self.assertEqual(client.consumer_token, consumer_token)
        self.assertEqual(client.secret, secret)
        self.assertIsInstance(client.session, OAuth1Session)

    def test_init_trailing_slash_removal(self):
        """Test that trailing slashes are removed from host."""
        host = "http://maas.example.com:5240/MAAS/"
        client = MaasClient(host, "key", "token", "secret")

        # Verify trailing slash is removed
        self.assertEqual(client.host, "http://maas.example.com:5240/MAAS")

    def test_init_oauth_session_setup(self):
        """Test OAuth session setup during initialization"""
        client = MaasClient("http://test.maas", "key", "token", "secret")

        # Verify session is OAuth1Session
        self.assertIsInstance(client.session, OAuth1Session)

        # Verify OAuth credentials are set correctly
        oauth_auth = client.session.auth
        self.assertEqual(oauth_auth.client.client_key, "key")
        self.assertEqual(oauth_auth.client.resource_owner_key, "token")
        self.assertEqual(oauth_auth.client.resource_owner_secret, "secret")


class TestMaasClientMachineOperations(unittest.TestCase):
    """Test MaasClient machine management operations."""

    def setUp(self):
        """Set up test client."""
        self.client = MaasClient("http://maas.test", "key", "token", "secret")

    def test_extract_owner_name_dict(self):
        """Test _extract_owner_name with dict owner."""
        machine = {"owner": {"username": "testuser"}}
        result = self.client._extract_owner_name(machine)
        self.assertEqual(result, "testuser")

    def test_extract_owner_name_string(self):
        """Test _extract_owner_name with string owner."""
        machine = {"owner": "testuser"}
        result = self.client._extract_owner_name(machine)
        self.assertEqual(result, "testuser")

    def test_extract_owner_name_none(self):
        """Test _extract_owner_name with no owner."""
        machine = {}
        result = self.client._extract_owner_name(machine)
        self.assertEqual(result, "None")

        # Test with None owner
        machine = {"owner": None}
        result = self.client._extract_owner_name(machine)
        self.assertEqual(result, "None")

    def test_extract_owner_name_dict_no_username(self):
        """Test _extract_owner_name with dict owner missing username."""
        machine = {"owner": {"id": 1}}
        result = self.client._extract_owner_name(machine)
        self.assertEqual(result, "None")

    @patch.object(OAuth1Session, "get")
    def test_get_machines_success(self, mock_get):
        """Test successful get_machines operation."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = [
            {"system_id": "test1", "hostname": "node1"},
            {"system_id": "test2", "hostname": "node2"},
        ]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test get_machines
        result = self.client.get_machines()

        # Verify call and result
        mock_get.assert_called_once_with("http://maas.test/api/2.0/machines/")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["system_id"], "test1")

    @patch.object(OAuth1Session, "get")
    def test_get_machines_failure(self, mock_get):
        """Test get_machines with API failure."""
        # Mock failed response
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        # Test get_machines failure
        with patch("builtins.print") as mock_print:
            result = self.client.get_machines()

        # Verify error handling
        self.assertEqual(result, [])
        mock_print.assert_called_with("Failed to get machines from MAAS: API Error")

    @patch.object(OAuth1Session, "get")
    def test_get_machine_success(self, mock_get):
        """Test successful get_machine operation."""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {"system_id": "test1", "hostname": "node1"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Test get_machine
        result = self.client.get_machine("test1")

        # Verify call and result
        mock_get.assert_called_once_with("http://maas.test/api/2.0/machines/test1/")
        self.assertEqual(result["system_id"], "test1")

    @patch.object(OAuth1Session, "get")
    def test_get_machine_failure(self, mock_get):
        """Test get_machine with API failure."""
        # Mock failed response
        mock_get.side_effect = requests.exceptions.RequestException("API Error")

        # Test get_machine failure
        with patch("builtins.print") as mock_print:
            result = self.client.get_machine("test1")

        # Verify error handling
        self.assertIsNone(result)
        mock_print.assert_called_with("Failed to get machine test1: API Error")

    @patch.object(OAuth1Session, "post")
    def test_commission_machine_success(self, mock_post):
        """Test successful commission_machine operation."""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Test commission_machine
        with patch("builtins.print") as mock_print:
            result = self.client.commission_machine("test1")

        # Verify call and result
        mock_post.assert_called_once_with(
            "http://maas.test/api/2.0/machines/test1/op-commission",
            data={"enable_ssh": 1},
        )
        self.assertTrue(result)
        mock_print.assert_called_with("Successfully commissioned machine test1")

    @patch.object(OAuth1Session, "post")
    def test_commission_machine_without_ssh(self, mock_post):
        """Test commission_machine with SSH disabled."""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Test commission_machine without SSH
        result = self.client.commission_machine("test1", enable_ssh=False)

        # Verify SSH disabled
        mock_post.assert_called_once_with(
            "http://maas.test/api/2.0/machines/test1/op-commission",
            data={"enable_ssh": 0},
        )
        self.assertTrue(result)

    @patch.object(OAuth1Session, "post")
    def test_commission_machine_failure(self, mock_post):
        """Test commission_machine with API failure."""
        # Mock failed response
        mock_post.side_effect = requests.exceptions.RequestException("API Error")

        # Test commission_machine failure
        with patch("builtins.print") as mock_print:
            result = self.client.commission_machine("test1")

        # Verify error handling
        self.assertFalse(result)
        mock_print.assert_called_with("Failed to commission machine test1: API Error")

    @patch.object(MaasClient, "get_machine")
    @patch.object(MaasClient, "release_machine")
    @patch.object(OAuth1Session, "post")
    @patch("time.sleep")
    def test_force_commission_machine_deployed_state(
        self, mock_sleep, mock_post, mock_release, mock_get_machine
    ):
        """Test force_commission_machine with deployed machine."""
        # Mock machine in deployed state
        mock_get_machine.return_value = {
            "system_id": "test1",
            "status_name": "Deployed",
        }
        mock_release.return_value = True

        # Mock successful commission response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Test force commission
        with patch("builtins.print") as mock_print:
            result = self.client.force_commission_machine("test1")

        # Verify flow
        mock_get_machine.assert_called_once_with("test1")
        mock_release.assert_called_once_with("test1")
        mock_sleep.assert_called_once_with(2)
        mock_post.assert_called_with(
            "http://maas.test/api/2.0/machines/test1/op-commission",
            data={"enable_ssh": 1},
        )
        self.assertTrue(result)

    @patch.object(MaasClient, "get_machine")
    def test_force_commission_machine_not_found(self, mock_get_machine):
        """Test force_commission_machine with machine not found."""
        # Mock machine not found
        mock_get_machine.return_value = None

        # Test force commission
        with patch("builtins.print") as mock_print:
            result = self.client.force_commission_machine("test1")

        # Verify failure
        self.assertFalse(result)
        mock_print.assert_called_with("Machine test1 not found")

    @patch.object(OAuth1Session, "post")
    def test_abort_machine_operation_success(self, mock_post):
        """Test successful abort_machine_operation."""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Test abort operation
        with patch("builtins.print") as mock_print:
            result = self.client.abort_machine_operation("test1")

        # Verify call and result
        mock_post.assert_called_once_with(
            "http://maas.test/api/2.0/machines/test1/op-abort"
        )
        self.assertTrue(result)
        mock_print.assert_called_with(
            "Successfully aborted operations on machine test1"
        )

    @patch.object(OAuth1Session, "post")
    def test_abort_machine_operation_failure(self, mock_post):
        """Test abort_machine_operation with API failure."""
        # Mock failed response
        mock_post.side_effect = requests.exceptions.RequestException("API Error")

        # Test abort operation failure
        with patch("builtins.print") as mock_print:
            result = self.client.abort_machine_operation("test1")

        # Verify error handling
        self.assertFalse(result)
        mock_print.assert_called_with(
            "Failed to abort operations on machine test1: API Error"
        )

    @patch.object(OAuth1Session, "post")
    def test_deploy_machine_success(self, mock_post):
        """Test successful deploy_machine operation."""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Test deploy machine
        with patch("builtins.print") as mock_print:
            result = self.client.deploy_machine("test1")

        # Verify call and result
        mock_post.assert_called_once_with(
            "http://maas.test/api/2.0/machines/test1/op-deploy", data={}
        )
        self.assertTrue(result)
        mock_print.assert_called_with("Successfully deployed machine test1")

    @patch.object(OAuth1Session, "post")
    def test_deploy_machine_with_os(self, mock_post):
        """Test deploy_machine with specific OS."""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Test deploy machine with OS
        result = self.client.deploy_machine("test1", os_name="ubuntu")

        # Verify OS parameter
        mock_post.assert_called_once_with(
            "http://maas.test/api/2.0/machines/test1/op-deploy",
            data={"distro_series": "ubuntu"},
        )
        self.assertTrue(result)

    @patch.object(OAuth1Session, "post")
    def test_release_machine_success(self, mock_post):
        """Test successful release_machine operation."""
        # Mock successful response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        # Test release machine
        with patch("builtins.print") as mock_print:
            result = self.client.release_machine("test1")

        # Verify call and result
        mock_post.assert_called_once_with(
            "http://maas.test/api/2.0/machines/test1/op-release"
        )
        self.assertTrue(result)
        mock_print.assert_called_with("Successfully released machine test1")


class TestMaasClientStatusOperations(unittest.TestCase):
    """Test MaasClient status and filtering operations."""

    def setUp(self):
        """Set up test client."""
        self.client = MaasClient("http://maas.test", "key", "token", "secret")

    @patch.object(MaasClient, "get_machine")
    def test_get_machine_status_success(self, mock_get_machine):
        """Test successful get_machine_status."""
        mock_get_machine.return_value = {"status_name": "Ready"}

        result = self.client.get_machine_status("test1")

        self.assertEqual(result, "Ready")
        mock_get_machine.assert_called_once_with("test1")

    @patch.object(MaasClient, "get_machine")
    def test_get_machine_status_not_found(self, mock_get_machine):
        """Test get_machine_status with machine not found."""
        mock_get_machine.return_value = None

        result = self.client.get_machine_status("test1")

        self.assertIsNone(result)

    @patch.object(MaasClient, "get_machine")
    def test_get_machine_ip_success(self, mock_get_machine):
        """Test successful get_machine_ip."""
        mock_get_machine.return_value = {
            "interface_set": [{"discovered": [{"ip_address": "192.168.1.100"}]}]
        }

        result = self.client.get_machine_ip("test1")

        self.assertEqual(result, "192.168.1.100")

    @patch.object(MaasClient, "get_machine")
    def test_get_machine_ip_no_interface(self, mock_get_machine):
        """Test get_machine_ip with no interfaces."""
        mock_get_machine.return_value = {"interface_set": None}

        result = self.client.get_machine_ip("test1")

        self.assertIsNone(result)

    @patch.object(MaasClient, "get_machine")
    def test_get_machine_ip_no_discovered(self, mock_get_machine):
        """Test get_machine_ip with no discovered IPs."""
        mock_get_machine.return_value = {"interface_set": [{"discovered": None}]}

        result = self.client.get_machine_ip("test1")

        self.assertIsNone(result)

    @patch.object(MaasClient, "get_machines")
    def test_get_machines_by_status(self, mock_get_machines):
        """Test get_machines_by_status filtering."""
        mock_get_machines.return_value = [
            {"system_id": "test1", "status_name": "Ready"},
            {"system_id": "test2", "status_name": "Deployed"},
            {"system_id": "test3", "status_name": "Ready"},
        ]

        result = self.client.get_machines_by_status("Ready")

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["system_id"], "test1")
        self.assertEqual(result[1]["system_id"], "test3")

    @patch.object(MaasClient, "get_machines_by_status")
    def test_get_ready_machines(self, mock_get_by_status):
        """Test get_ready_machines shortcut."""
        mock_get_by_status.return_value = [{"system_id": "test1"}]

        result = self.client.get_ready_machines()

        mock_get_by_status.assert_called_once_with("Ready")
        self.assertEqual(len(result), 1)

    @patch.object(MaasClient, "get_machines_by_status")
    def test_get_deployed_machines(self, mock_get_by_status):
        """Test get_deployed_machines shortcut."""
        mock_get_by_status.return_value = [{"system_id": "test1"}]

        result = self.client.get_deployed_machines()

        mock_get_by_status.assert_called_once_with("Deployed")
        self.assertEqual(len(result), 1)

    @patch.object(MaasClient, "get_machines")
    def test_get_available_machines(self, mock_get_machines):
        """Test get_available_machines filtering."""
        mock_get_machines.return_value = [
            {"system_id": "test1", "status_name": "Ready"},
            {"system_id": "test2", "status_name": "Deployed"},
            {"system_id": "test3", "status_name": "New"},
            {"system_id": "test4", "status_name": "Failed commissioning"},
            {"system_id": "test5", "status_name": "Failed testing"},
        ]

        result = self.client.get_available_machines()

        # Should return Ready, New, Failed commissioning, Failed testing
        self.assertEqual(len(result), 4)
        available_ids = [m["system_id"] for m in result]
        self.assertIn("test1", available_ids)
        self.assertIn("test3", available_ids)
        self.assertIn("test4", available_ids)
        self.assertIn("test5", available_ids)
        self.assertNotIn("test2", available_ids)  # Deployed should be excluded


class TestMaasClientNetworkOperations(unittest.TestCase):
    """Test MaasClient network and IP extraction operations."""

    def setUp(self):
        """Set up test client."""
        self.client = MaasClient("http://maas.test", "key", "token", "secret")

    def test_extract_ip_addresses_discovered(self):
        """Test _extract_ip_addresses with discovered IPs."""
        machine = {
            "interface_set": [
                {
                    "discovered": [
                        {"ip_address": "192.168.1.100"},
                        {"ip_address": "192.168.1.101"},
                    ]
                }
            ]
        }

        result = self.client._extract_ip_addresses(machine)

        self.assertEqual(len(result), 2)
        self.assertIn("192.168.1.100", result)
        self.assertIn("192.168.1.101", result)

    def test_extract_ip_addresses_links(self):
        """Test _extract_ip_addresses with static links."""
        machine = {
            "interface_set": [
                {"links": [{"ip_address": "10.0.0.100"}, {"ip_address": "10.0.0.101"}]}
            ]
        }

        result = self.client._extract_ip_addresses(machine)

        self.assertEqual(len(result), 2)
        self.assertIn("10.0.0.100", result)
        self.assertIn("10.0.0.101", result)

    def test_extract_ip_addresses_mixed(self):
        """Test _extract_ip_addresses with both discovered and links."""
        machine = {
            "interface_set": [
                {
                    "discovered": [{"ip_address": "192.168.1.100"}],
                    "links": [{"ip_address": "10.0.0.100"}],
                }
            ]
        }

        result = self.client._extract_ip_addresses(machine)

        self.assertEqual(len(result), 2)
        self.assertIn("192.168.1.100", result)
        self.assertIn("10.0.0.100", result)

    def test_extract_ip_addresses_duplicates(self):
        """Test _extract_ip_addresses removes duplicates."""
        machine = {
            "interface_set": [
                {
                    "discovered": [{"ip_address": "192.168.1.100"}],
                    "links": [{"ip_address": "192.168.1.100"}],
                }
            ]
        }

        result = self.client._extract_ip_addresses(machine)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "192.168.1.100")

    def test_extract_ip_addresses_none_values(self):
        """Test _extract_ip_addresses with None values."""
        machine = {
            "interface_set": [
                None,  # None interface
                {"discovered": None, "links": [None, {"ip_address": "10.0.0.100"}]},
            ]
        }

        result = self.client._extract_ip_addresses(machine)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], "10.0.0.100")

    def test_extract_ip_addresses_no_interfaces(self):
        """Test _extract_ip_addresses with no interface_set."""
        machine = {"interface_set": None}

        result = self.client._extract_ip_addresses(machine)

        self.assertEqual(result, [])


class TestMaasClientSummaryOperations(unittest.TestCase):
    """Test MaasClient summary and detailed information operations."""

    def setUp(self):
        """Set up test client."""
        self.client = MaasClient("http://maas.test", "key", "token", "secret")

    @patch.object(MaasClient, "get_machines")
    @patch.object(MaasClient, "_extract_ip_addresses")
    def test_get_machines_summary(self, mock_extract_ips, mock_get_machines):
        """Test get_machines_summary operation."""
        # Mock machines data
        mock_get_machines.return_value = [
            {
                "system_id": "test1",
                "hostname": "node1",
                "status_name": "Ready",
                "architecture": "amd64/generic",
                "cpu_count": 4,
                "memory": 8192,  # MB
                "blockdevice_set": [{"size": 1000000000000}],  # 1TB
                "power_type": "ipmi",
                "tag_names": [{"name": "rack1"}],
                "owner": {"username": "admin"},
                "created": "2023-01-01T00:00:00Z",
                "updated": "2023-01-02T00:00:00Z",
                "bios_boot_method": "uefi",
            }
        ]

        mock_extract_ips.return_value = ["192.168.1.100"]

        result = self.client.get_machines_summary()

        # Verify summary structure
        self.assertEqual(len(result), 1)
        machine = result[0]

        self.assertEqual(machine["system_id"], "test1")
        self.assertEqual(machine["hostname"], "node1")
        self.assertEqual(machine["status"], "Ready")
        self.assertEqual(machine["cpu_count"], 4)
        self.assertEqual(machine["memory"], 8192)
        self.assertEqual(machine["storage"], 1000000000000)
        self.assertEqual(machine["storage_display"], "931.3 GB")
        self.assertEqual(machine["memory_display"], "8.0 GB")
        self.assertEqual(machine["ip_addresses"], ["192.168.1.100"])
        self.assertEqual(machine["tags"], ["rack1"])
        self.assertEqual(machine["owner"], "admin")

    @patch.object(MaasClient, "get_machine")
    @patch.object(MaasClient, "_extract_ip_addresses")
    def test_get_machine_details_success(self, mock_extract_ips, mock_get_machine):
        """Test successful get_machine_details operation."""
        # Mock machine data
        mock_get_machine.return_value = {
            "system_id": "test1",
            "hostname": "node1",
            "status_name": "Ready",
            "architecture": "amd64/generic",
            "cpu_count": 4,
            "memory": 8192,
            "power_type": "ipmi",
            "bios_boot_method": "uefi",
            "owner": {"username": "admin"},
            "created": "2023-01-01T00:00:00Z",
            "updated": "2023-01-02T00:00:00Z",
            "blockdevice_set": [
                {
                    "name": "sda",
                    "model": "Samsung SSD",
                    "size": 1000000000000,
                    "block_size": 4096,
                    "type": "physical",
                }
            ],
            "boot_interface": {"name": "eth0"},
            "tag_names": [{"name": "rack1"}],
        }

        mock_extract_ips.return_value = ["192.168.1.100"]

        result = self.client.get_machine_details("test1")

        # Verify detailed structure
        self.assertIsNotNone(result)
        self.assertEqual(result["basic_info"]["system_id"], "test1")
        self.assertEqual(result["basic_info"]["hostname"], "node1")
        self.assertEqual(result["hardware"]["cpu_count"], 4)
        self.assertEqual(result["hardware"]["memory"], 8192)
        self.assertEqual(len(result["hardware"]["storage_devices"]), 1)

        storage = result["hardware"]["storage_devices"][0]
        self.assertEqual(storage["name"], "sda")
        self.assertEqual(storage["model"], "Samsung SSD")
        self.assertEqual(storage["size_display"], "931.3 GB")

        self.assertEqual(result["network"]["ip_addresses"], ["192.168.1.100"])
        self.assertEqual(result["network"]["boot_interface"], "eth0")
        self.assertEqual(result["tags"], ["rack1"])

    @patch.object(MaasClient, "get_machine")
    def test_get_machine_details_not_found(self, mock_get_machine):
        """Test get_machine_details with machine not found."""
        mock_get_machine.return_value = None

        result = self.client.get_machine_details("test1")

        self.assertIsNone(result)


class TestMaasClientErrorHandling(unittest.TestCase):
    """Test MaasClient error handling scenarios."""

    def setUp(self):
        """Set up test client."""
        self.client = MaasClient("http://maas.test", "key", "token", "secret")

    @patch.object(OAuth1Session, "post")
    def test_deploy_machine_failure(self, mock_post):
        """Test deploy_machine with API failure."""
        # Mock failed response
        mock_post.side_effect = requests.exceptions.RequestException("Deploy failed")

        # Test deploy machine failure
        with patch("builtins.print") as mock_print:
            result = self.client.deploy_machine("test1")

        # Verify error handling
        self.assertFalse(result)
        mock_print.assert_called_with("Failed to deploy machine test1: Deploy failed")

    @patch.object(OAuth1Session, "post")
    def test_release_machine_failure(self, mock_post):
        """Test release_machine with API failure."""
        # Mock failed response
        mock_post.side_effect = requests.exceptions.RequestException("Release failed")

        # Test release machine failure
        with patch("builtins.print") as mock_print:
            result = self.client.release_machine("test1")

        # Verify error handling
        self.assertFalse(result)
        mock_print.assert_called_with("Failed to release machine test1: Release failed")

    @patch.object(MaasClient, "get_machine")
    @patch.object(MaasClient, "release_machine")
    def test_force_commission_release_failure(self, mock_release, mock_get_machine):
        """Test force_commission_machine with release failure."""
        # Mock machine in deployed state
        mock_get_machine.return_value = {
            "system_id": "test1",
            "status_name": "Deployed",
        }
        mock_release.return_value = False  # Release fails

        # Test force commission
        with patch("builtins.print") as mock_print:
            result = self.client.force_commission_machine("test1")

        # Verify failure
        self.assertFalse(result)
        mock_print.assert_called_with("Failed to release machine test1")


if __name__ == "__main__":
    unittest.main()
