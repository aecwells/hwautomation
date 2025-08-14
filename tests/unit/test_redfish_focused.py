"""
Focused test suite for the Redfish components that provides good coverage.

This module tests the key Redfish components that are working:
- RedfishCoordinator basic functionality
- Import compatibility
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from hwautomation.hardware.redfish.managers import (
    RedfishCoordinator,
)


class TestRedfishCoordinator:
    """Test suite for RedfishCoordinator basic functionality."""

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


class TestBackwardCompatibility:
    """Test suite for backward compatibility of refactored Redfish components."""

    def test_redfish_manager_import_compatibility(self):
        """Test that old RedfishManager import still works."""
        # This should work without modification
        from hwautomation.hardware.redfish.manager import RedfishManager
        from hwautomation.hardware.redfish.managers import RedfishCoordinator

        # Should be aliased to the same class
        assert RedfishManager is RedfishCoordinator


if __name__ == "__main__":
    pytest.main([__file__])
