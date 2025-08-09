"""HPE-specific hardware discovery implementation."""

import re
from typing import Any, Dict, List

from ..base import SystemInfo
from .base import BaseVendorHandler


class HPEDiscovery(BaseVendorHandler):
    """HPE-specific hardware discovery."""

    def can_handle(self, system_info: SystemInfo) -> bool:
        """Check if this is an HPE system."""
        if not system_info.manufacturer:
            return False
        manufacturer = system_info.manufacturer.lower()
        return any(vendor in manufacturer for vendor in ["hpe", "hewlett", "hp"])

    def get_priority(self) -> int:
        """Higher priority for HPE systems."""
        return 10

    def install_vendor_tools(self) -> bool:
        """Install HPE management tools."""
        return self.tool_installer.install_hpe_tools()

    def _run_vendor_discovery(self, errors: list) -> Dict[str, Any]:
        """Run HPE-specific discovery."""
        hpe_info = {}

        # Check for HPE management tools
        hpe_tool = self._find_hpe_tool()
        if hpe_tool:
            controller_info = self._get_controller_info(hpe_tool, errors)
            hpe_info.update(controller_info)

        # Check for iLO information
        ilo_info = self._get_ilo_info(errors)
        hpe_info.update(ilo_info)

        return hpe_info

    def _find_hpe_tool(self) -> str:
        """Find available HPE management tool."""
        hpe_tools = ["hpssacli", "ssacli", "hpacucli"]

        for tool in hpe_tools:
            if self.ssh_runner.check_tool_availability(tool):
                return tool

        return ""

    def _get_controller_info(self, hpe_tool: str, errors: list) -> Dict[str, Any]:
        """Get storage controller information."""
        stdout, stderr, exit_code = self.ssh_runner.run_command(
            f"{hpe_tool} ctrl all show config", use_sudo=True
        )

        if exit_code == 0:
            return self._parse_hpe_controller_info(stdout)
        else:
            errors.append(f"{hpe_tool} controller query failed: {stderr}")
            return {}

    def _get_ilo_info(self, errors: list) -> Dict[str, Any]:
        """Get iLO information from DMI."""
        stdout, stderr, exit_code = self.ssh_runner.run_command(
            "dmidecode -t 38 | grep -i ilo", use_sudo=True
        )

        ilo_info = {}
        if exit_code == 0 and stdout.strip():
            ilo_info["ilo_present"] = True
            # Try to extract iLO version or details
            for line in stdout.split("\n"):
                if "ilo" in line.lower():
                    ilo_info["ilo_details"] = line.strip()
                    break

        return ilo_info

    def _parse_hpe_controller_info(self, output: str) -> Dict[str, Any]:
        """Parse HPE storage controller information."""
        controller_info = {}

        # Look for controller lines
        controllers: List[Dict[str, Any]] = []
        current_controller: Dict[str, Any] = {}

        for line in output.split("\n"):
            line = line.strip()

            # Controller line (e.g., "Smart Array P440ar in Slot 0")
            if "smart array" in line.lower() or "controller" in line.lower():
                if current_controller:  # Only append if it has content
                    controllers.append(current_controller)

                current_controller = {"name": line, "drives": [], "arrays": []}

            # Drive information
            elif "physicaldrive" in line.lower() and current_controller:
                current_controller["drives"].append(line)

            # Array information
            elif "array" in line.lower() and current_controller:
                current_controller["arrays"].append(line)

        if current_controller:  # Only append if it has content
            controllers.append(current_controller)

        if controllers:
            controller_info["storage_controllers"] = controllers
            controller_info["controller_count"] = len(controllers)

        return controller_info
