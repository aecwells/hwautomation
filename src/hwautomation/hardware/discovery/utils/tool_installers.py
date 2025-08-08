"""Tool installation utilities for vendor-specific discovery tools."""

from typing import Dict

from ....logging import get_logger
from .ssh_commands import SSHCommandRunner

logger = get_logger(__name__)


class VendorToolInstaller:
    """Manages installation of vendor-specific tools."""

    def __init__(self, ssh_runner: SSHCommandRunner):
        """Initialize with SSH command runner."""
        self.ssh_runner = ssh_runner
        self.logger = get_logger(__name__)

    def install_for_vendor(self, vendor: str) -> bool:
        """Install tools for a specific vendor."""
        vendor_lower = vendor.lower()

        if "supermicro" in vendor_lower:
            return self.install_supermicro_tools()
        elif "hpe" in vendor_lower or "hewlett" in vendor_lower:
            return self.install_hpe_tools()
        elif "dell" in vendor_lower:
            return self.install_dell_tools()
        else:
            self.logger.info(f"No specific tools available for vendor: {vendor}")
            return True  # Not an error, just no vendor-specific tools

    def install_supermicro_tools(self) -> bool:
        """Install Supermicro SUM tool."""
        if self.ssh_runner.check_tool_availability("sum"):
            self.logger.info("Supermicro SUM tool already available")
            return True

        self.logger.warning("Supermicro SUM tool not available for auto-install")
        self.logger.info(
            "Manual installation required: download from Supermicro website"
        )
        return False

    def install_hpe_tools(self) -> bool:
        """Install HPE management tools."""
        tools = ["hpacucli", "ssacli"]

        for tool in tools:
            if self.ssh_runner.check_tool_availability(tool):
                self.logger.info(f"HPE tool {tool} already available")
                return True

        self.logger.warning("HPE management tools not available for auto-install")
        self.logger.info("Manual installation required: download from HPE website")
        return False

    def install_dell_tools(self) -> bool:
        """Install Dell management tools."""
        if self.ssh_runner.check_tool_availability("racadm"):
            self.logger.info("Dell RACADM tool already available")
            return True

        self.logger.warning("Dell RACADM tool not available for auto-install")
        self.logger.info("Manual installation required: download from Dell website")
        return False

    def get_installation_status(self) -> Dict[str, Dict[str, bool]]:
        """Get status of all vendor tools."""
        return {
            "supermicro": {
                "sum": self.ssh_runner.check_tool_availability("sum"),
            },
            "hpe": {
                "hpacucli": self.ssh_runner.check_tool_availability("hpacucli"),
                "ssacli": self.ssh_runner.check_tool_availability("ssacli"),
            },
            "dell": {
                "racadm": self.ssh_runner.check_tool_availability("racadm"),
            },
            "common": {
                "ipmitool": self.ssh_runner.check_tool_availability("ipmitool"),
                "dmidecode": self.ssh_runner.check_tool_availability("dmidecode"),
            },
        }
