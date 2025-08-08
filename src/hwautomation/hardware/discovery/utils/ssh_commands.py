"""SSH command utilities for hardware discovery."""

from typing import Any, Dict, Optional, Tuple

from ....logging import get_logger
from ....utils.network import SSHClient

logger = get_logger(__name__)


class SSHCommandRunner:
    """Utility class for running common discovery commands via SSH."""

    def __init__(self, ssh_client: SSHClient):
        """Initialize with SSH client."""
        self.ssh_client = ssh_client
        self.logger = get_logger(__name__)

    def run_command(self, command: str, use_sudo: bool = False) -> Tuple[str, str, int]:
        """Run a command via SSH and return stdout, stderr, exit_code."""
        if use_sudo:
            command = f"sudo {command}"

        return self.ssh_client.exec_command(command)

    def run_dmidecode(self, table_type: str) -> Tuple[str, str, int]:
        """Run dmidecode command for specific table type."""
        return self.run_command(f"dmidecode -t {table_type}", use_sudo=True)

    def run_ipmitool(self, subcommand: str) -> Tuple[str, str, int]:
        """Run ipmitool command."""
        return self.run_command(f"ipmitool {subcommand}")

    def check_tool_availability(self, tool_name: str) -> bool:
        """Check if a tool is available on the system."""
        stdout, stderr, exit_code = self.run_command(f"which {tool_name}")
        return exit_code == 0

    def install_package(self, package_name: str) -> bool:
        """Install a package using apt."""
        stdout, stderr, exit_code = self.run_command(
            f"apt-get update && apt-get install -y {package_name}", use_sudo=True
        )
        success = exit_code == 0
        if not success:
            self.logger.warning(f"Failed to install {package_name}: {stderr}")
        return success

    def get_network_interfaces(self) -> Tuple[str, str, int]:
        """Get network interface information."""
        return self.run_command("ip addr show")

    def get_cpu_info(self) -> Tuple[str, str, int]:
        """Get CPU information."""
        return self.run_command("lscpu")

    def get_memory_info(self) -> Tuple[str, str, int]:
        """Get memory information."""
        return self.run_command("free -h")

    def get_vendor_tool_output(self, vendor: str, command: str) -> Tuple[str, str, int]:
        """Run vendor-specific tool commands."""
        vendor_commands = {
            "supermicro": {
                "system_info": "sum -c QuerySystemInfo",
                "bios_info": "sum -c GetBiosInfo",
                "bmc_info": "sum -c GetBmcInfo",
            },
            "hpe": {
                "controller_info": "hpacucli controller all show config",
            },
            "dell": {
                "chassis_info": "racadm get System.ServerTopology",
            },
        }

        if vendor.lower() in vendor_commands:
            vendor_cmd = vendor_commands[vendor.lower()].get(command)
            if vendor_cmd:
                return self.run_command(vendor_cmd)

        self.logger.warning(f"Unknown vendor command: {vendor}.{command}")
        return "", f"Unknown vendor command: {vendor}.{command}", 1


class ToolInstaller:
    """Utility class for installing vendor-specific tools."""

    def __init__(self, ssh_runner: SSHCommandRunner):
        """Initialize with SSH command runner."""
        self.ssh_runner = ssh_runner
        self.logger = get_logger(__name__)

    def install_ipmitool(self) -> bool:
        """Install ipmitool if not present."""
        if self.ssh_runner.check_tool_availability("ipmitool"):
            return True

        self.logger.info("Installing ipmitool...")
        return self.ssh_runner.install_package("ipmitool")

    def install_supermicro_tools(self) -> bool:
        """Install Supermicro SUM tool."""
        if self.ssh_runner.check_tool_availability("sum"):
            return True

        self.logger.info("Supermicro SUM tool not available for auto-install")
        return False

    def install_hpe_tools(self) -> bool:
        """Install HPE management tools."""
        if self.ssh_runner.check_tool_availability("hpacucli"):
            return True

        self.logger.info("HPE tools not available for auto-install")
        return False

    def install_dell_tools(self) -> bool:
        """Install Dell management tools."""
        if self.ssh_runner.check_tool_availability("racadm"):
            return True

        self.logger.info("Dell RACADM tool not available for auto-install")
        return False

    def ensure_basic_tools(self) -> Dict[str, bool]:
        """Ensure basic discovery tools are available."""
        results = {
            "ipmitool": self.install_ipmitool(),
        }

        # dmidecode is usually pre-installed on most systems
        results["dmidecode"] = self.ssh_runner.check_tool_availability("dmidecode")

        return results
