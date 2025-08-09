"""Dell-specific hardware discovery implementation."""

import re
from typing import Any, Dict

from ..base import SystemInfo
from .base import BaseVendorHandler


class DellDiscovery(BaseVendorHandler):
    """Dell-specific hardware discovery."""

    def can_handle(self, system_info: SystemInfo) -> bool:
        """Check if this is a Dell system."""
        if not system_info.manufacturer:
            return False
        return "dell" in system_info.manufacturer.lower()

    def get_priority(self) -> int:
        """Higher priority for Dell systems."""
        return 10

    def install_vendor_tools(self) -> bool:
        """Install Dell management tools."""
        return self.tool_installer.install_dell_tools()

    def _run_vendor_discovery(self, errors: list) -> Dict[str, Any]:
        """Run Dell-specific discovery."""
        dell_info = {}

        # Check for Dell OpenManage tools
        if self.ssh_runner.check_tool_availability("omreport"):
            chassis_info = self._get_chassis_info(errors)
            dell_info.update(chassis_info)

        # Check for RACADM tool
        if self.ssh_runner.check_tool_availability("racadm"):
            rac_info = self._get_rac_info(errors)
            dell_info.update(rac_info)

        # Check for Dell service tag in DMI
        service_tag_info = self._get_service_tag_info(errors)
        dell_info.update(service_tag_info)

        return dell_info

    def _get_chassis_info(self, errors: list) -> Dict[str, Any]:
        """Get chassis information using omreport."""
        stdout, stderr, exit_code = self.ssh_runner.run_command(
            "omreport chassis info", use_sudo=True
        )

        if exit_code == 0:
            return self._parse_dell_chassis_info(stdout)
        else:
            errors.append(f"omreport chassis failed: {stderr}")
            return {}

    def _get_rac_info(self, errors: list) -> Dict[str, Any]:
        """Get DRAC/iDRAC information using racadm."""
        commands = [
            ("racadm getniccfg", "nic_config"),
            ("racadm get System.ServerTopology", "server_topology"),
        ]

        rac_info = {}
        for command, key in commands:
            stdout, stderr, exit_code = self.ssh_runner.run_command(
                command, use_sudo=True
            )

            if exit_code == 0:
                rac_info[key] = stdout.strip()
            else:
                errors.append(f"{command} failed: {stderr}")

        return rac_info

    def _get_service_tag_info(self, errors: list) -> Dict[str, Any]:
        """Get Dell service tag from DMI."""
        stdout, stderr, exit_code = self.ssh_runner.run_command(
            "dmidecode -s system-serial-number", use_sudo=True
        )

        service_tag_info = {}
        if exit_code == 0 and stdout.strip():
            service_tag = stdout.strip()
            # Dell service tags are typically 7 characters
            if len(service_tag) == 7 and service_tag.isalnum():
                service_tag_info["dell_service_tag"] = service_tag

        return service_tag_info

    def _parse_dell_chassis_info(self, output: str) -> Dict[str, Any]:
        """Parse Dell chassis information."""
        chassis_info = {}

        for line in output.split("\n"):
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()

                # Map common Dell chassis fields
                field_mappings = {
                    "chassis_model": "chassis_model",
                    "chassis_service_tag": "chassis_service_tag",
                    "chassis_asset_tag": "chassis_asset_tag",
                    "power_supply_count": "power_supply_count",
                    "cooling_device_count": "cooling_device_count",
                }

                if key in field_mappings:
                    chassis_info[f"dell_{field_mappings[key]}"] = value

        return chassis_info
