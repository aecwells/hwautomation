"""Base vendor discovery implementation."""

from abc import ABC, abstractmethod
from typing import Any, Dict

from ..base import BaseVendorDiscovery, SystemInfo
from ..utils.ssh_commands import SSHCommandRunner
from ..utils.tool_installers import VendorToolInstaller


class BaseVendorHandler(BaseVendorDiscovery):
    """Base implementation for vendor-specific discovery handlers."""

    def __init__(self, ssh_client):
        """Initialize vendor handler."""
        super().__init__(ssh_client)
        self.ssh_runner = SSHCommandRunner(ssh_client)
        self.tool_installer = VendorToolInstaller(self.ssh_runner)

    def install_vendor_tools(self) -> bool:
        """Install vendor tools if needed (default: no tools)."""
        return True

    def get_vendor_specific_info(self, system_info: SystemInfo) -> Dict[str, Any]:
        """Get vendor information (default: no vendor-specific info)."""
        return {}

    def discover_vendor_info(self, errors: list) -> Dict[str, Any]:
        """Template method for vendor discovery process."""
        vendor_info: Dict[str, Any] = {}

        # Install tools if needed
        if not self.install_vendor_tools():
            self.logger.warning("Failed to install vendor tools")
            return vendor_info

        # Run vendor-specific discovery
        try:
            vendor_info = self._run_vendor_discovery(errors)
        except Exception as e:
            self.logger.error(f"Vendor discovery failed: {e}")
            errors.append(f"Vendor discovery error: {e}")

        return vendor_info

    @abstractmethod
    def _run_vendor_discovery(self, errors: list) -> Dict[str, Any]:
        """Run vendor-specific discovery commands."""
        pass
