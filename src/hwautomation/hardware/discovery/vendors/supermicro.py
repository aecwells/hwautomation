"""Supermicro-specific hardware discovery implementation."""

import re
from typing import Any, Dict

from ..base import SystemInfo
from .base import BaseVendorHandler


class SupermicroDiscovery(BaseVendorHandler):
    """Supermicro-specific hardware discovery."""

    def can_handle(self, system_info: SystemInfo) -> bool:
        """Check if this is a Supermicro system."""
        if not system_info.manufacturer:
            return False
        return "supermicro" in system_info.manufacturer.lower()

    def get_priority(self) -> int:
        """Higher priority for Supermicro systems."""
        return 10

    def install_vendor_tools(self) -> bool:
        """Install Supermicro SUM tool."""
        return self.tool_installer.install_supermicro_tools()

    def _run_vendor_discovery(self, errors: list) -> Dict[str, Any]:
        """Run Supermicro-specific discovery."""
        supermicro_info: Dict[str, Any] = {}

        # Check for SUM tool variations
        sum_tool = self._find_sum_tool()
        if not sum_tool:
            errors.append("Supermicro SUM tool not found")
            return supermicro_info

        # Get system information
        system_info = self._get_system_info(sum_tool, errors)
        supermicro_info.update(system_info)

        # Get BIOS information
        bios_info = self._get_bios_info(sum_tool, errors)
        supermicro_info.update(bios_info)

        # Get BMC information
        bmc_info = self._get_bmc_info(sum_tool, errors)
        supermicro_info.update(bmc_info)

        return supermicro_info

    def _find_sum_tool(self) -> str:
        """Find available SUM tool variant."""
        sum_tools = ["sum", "sumtool", "/opt/supermicro/sum/sum"]

        for tool in sum_tools:
            if self.ssh_runner.check_tool_availability(tool):
                return tool

        return ""

    def _get_system_info(self, sum_tool: str, errors: list) -> Dict[str, Any]:
        """Get system information using SUM tool."""
        stdout, stderr, exit_code = self.ssh_runner.run_command(
            f"{sum_tool} -c GetSystemInfo", use_sudo=True
        )

        if exit_code == 0:
            return self._parse_sum_system_info(stdout)
        else:
            errors.append(f"SUM GetSystemInfo failed: {stderr}")
            return {}

    def _get_bios_info(self, sum_tool: str, errors: list) -> Dict[str, Any]:
        """Get BIOS information using SUM tool."""
        stdout, stderr, exit_code = self.ssh_runner.run_command(
            f"{sum_tool} -c GetBiosInfo", use_sudo=True
        )

        if exit_code == 0:
            return self._parse_sum_bios_info(stdout)
        else:
            errors.append(f"SUM GetBiosInfo failed: {stderr}")
            return {}

    def _get_bmc_info(self, sum_tool: str, errors: list) -> Dict[str, Any]:
        """Get BMC information using SUM tool."""
        stdout, stderr, exit_code = self.ssh_runner.run_command(
            f"{sum_tool} -c GetBmcInfo", use_sudo=True
        )

        if exit_code == 0:
            return self._parse_sum_bmc_info(stdout)
        else:
            errors.append(f"SUM GetBmcInfo failed: {stderr}")
            return {}

    def _parse_sum_system_info(self, output: str) -> Dict[str, Any]:
        """Parse SUM GetSystemInfo output."""
        info = {}

        for line in output.split("\n"):
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()

                if key in ["product_name", "serial_number", "manufacturer"]:
                    info[f"sum_{key}"] = value

        return info

    def _parse_sum_bios_info(self, output: str) -> Dict[str, Any]:
        """Parse SUM GetBiosInfo output."""
        info = {}

        for line in output.split("\n"):
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()

                if key in ["bios_version", "bios_date", "bios_revision"]:
                    info[f"sum_{key}"] = value

        return info

    def _parse_sum_bmc_info(self, output: str) -> Dict[str, Any]:
        """Parse SUM GetBmcInfo output."""
        info = {}

        for line in output.split("\n"):
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()

                if key in ["bmc_firmware_version", "bmc_ip_address", "bmc_mac_address"]:
                    info[f"sum_{key}"] = value

        return info
