"""Main hardware discovery manager module.

This module coordinates the hardware discovery process using
various parsers and vendor-specific handlers.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from ...logging import get_logger
from ...utils.network import SSHClient, SSHManager
from .base import (
    BaseVendorDiscovery,
    HardwareDiscovery,
    IPMIInfo,
    NetworkInterface,
    SystemInfo,
)
from .parsers import DmidecodeParser, IpmiParser, NetworkParser
from .utils import SSHCommandRunner, ToolInstaller
from .vendors import DellDiscovery, HPEDiscovery, SupermicroDiscovery

logger = get_logger(__name__)


class HardwareDiscoveryManager:
    """
    Manager for discovering hardware information from remote systems.

    This class coordinates the discovery process using modular parsers
    and vendor-specific handlers for comprehensive hardware information.
    """

    def __init__(self, ssh_manager: SSHManager):
        """
        Initialize hardware discovery manager.

        Args
        ----
        ssh_manager : SSHManager
            SSH manager for remote connections
        """
        self.ssh_manager = ssh_manager
        self.logger = get_logger(__name__)

        # Initialize parsers
        self.dmidecode_parser = DmidecodeParser()
        self.ipmi_parser = IpmiParser()
        self.network_parser = NetworkParser()

        # Initialize vendor handlers
        self.vendor_handlers: List[Type[BaseVendorDiscovery]] = [
            SupermicroDiscovery,
            HPEDiscovery,
            DellDiscovery,
        ]

    def discover_hardware(
        self, host: str, username: str = "ubuntu", key_file: str = None
    ) -> HardwareDiscovery:
        """
        Discover all hardware information from a remote system.

        Args
        ----
        host : str
            Target hostname or IP address
        username : str, optional
            SSH username (default: ubuntu)
        key_file : str, optional
            SSH private key file path

        Returns
        -------
        HardwareDiscovery
            Complete hardware discovery results
        """
        errors: List[str] = []

        try:
            # Connect to the system
            ssh_client = self.ssh_manager.connect(
                host=host, username=username, key_file=key_file, timeout=30
            )

            with ssh_client:
                # Discover system information
                system_info = self._discover_system_info(ssh_client, errors)

                # Discover IPMI information
                ipmi_info = self._discover_ipmi_info(ssh_client, errors)

                # Discover network interfaces
                network_interfaces = self._discover_network_interfaces(
                    ssh_client, errors
                )

                # Discover vendor-specific information
                vendor_info = self._discover_vendor_info(
                    ssh_client, system_info, errors
                )

                # Enhance system info with vendor data
                self._enhance_system_info(system_info, vendor_info)

                return HardwareDiscovery(
                    hostname=host,
                    system_info=system_info,
                    ipmi_info=ipmi_info,
                    network_interfaces=network_interfaces,
                    discovered_at=self._get_timestamp(),
                    discovery_errors=errors,
                )

        except Exception as e:
            self.logger.error(f"Hardware discovery failed for {host}: {e}")
            errors.append(f"Discovery failed: {str(e)}")

            # Return minimal discovery result with error
            return HardwareDiscovery(
                hostname=host,
                system_info=SystemInfo(),
                ipmi_info=IPMIInfo(),
                network_interfaces=[],
                discovered_at=self._get_timestamp(),
                discovery_errors=errors,
            )

    def _discover_system_info(
        self, ssh_client: SSHClient, errors: List[str]
    ) -> SystemInfo:
        """Discover system hardware information using dmidecode and basic tools."""
        system_info = SystemInfo()
        ssh_runner = SSHCommandRunner(ssh_client)

        try:
            # Get system information from dmidecode
            stdout, stderr, exit_code = ssh_runner.run_dmidecode("system")
            if exit_code == 0:
                system_info = self.dmidecode_parser.parse_system_info(stdout)
            else:
                errors.append(f"dmidecode system failed: {stderr}")

            # Get BIOS information
            stdout, stderr, exit_code = ssh_runner.run_dmidecode("bios")
            if exit_code == 0:
                bios_info = self.dmidecode_parser.parse_bios_info(stdout)
                system_info.bios_version = bios_info.get("version")
                system_info.bios_date = bios_info.get("date")
            else:
                errors.append(f"dmidecode bios failed: {stderr}")

            # Get CPU information
            stdout, stderr, exit_code = ssh_runner.get_cpu_info()
            if exit_code == 0:
                cpu_info = self.dmidecode_parser.parse_cpu_info(stdout)
                system_info.cpu_model = cpu_info.get("model")
                system_info.cpu_cores = cpu_info.get("cores")
            else:
                errors.append(f"lscpu failed: {stderr}")

            # Get memory information
            stdout, stderr, exit_code = ssh_runner.get_memory_info()
            if exit_code == 0:
                memory_info = self.dmidecode_parser.parse_memory_info(stdout)
                system_info.memory_total = memory_info.get("total")
            else:
                errors.append(f"memory info failed: {stderr}")

        except Exception as e:
            errors.append(f"System discovery failed: {str(e)}")

        return system_info

    def _discover_ipmi_info(self, ssh_client: SSHClient, errors: List[str]) -> IPMIInfo:
        """Discover IPMI/BMC information."""
        ssh_runner = SSHCommandRunner(ssh_client)
        tool_installer = ToolInstaller(ssh_runner)

        # Ensure ipmitool is available
        if not tool_installer.install_ipmitool():
            errors.append("Failed to install ipmitool")
            return IPMIInfo()

        try:
            # Get IPMI LAN configuration
            stdout, stderr, exit_code = ssh_runner.run_ipmitool("lan print 1")
            if exit_code == 0:
                return self.ipmi_parser.parse_lan_config(stdout)
            else:
                # Try channel 8 (common for some systems)
                stdout, stderr, exit_code = ssh_runner.run_ipmitool("lan print 8")
                if exit_code == 0:
                    ipmi_info = self.ipmi_parser.parse_lan_config(stdout)
                    ipmi_info.channel = 8
                    return ipmi_info
                else:
                    errors.append(f"IPMI lan print failed: {stderr}")

        except Exception as e:
            errors.append(f"IPMI discovery failed: {str(e)}")

        return IPMIInfo()

    def _discover_network_interfaces(
        self, ssh_client: SSHClient, errors: List[str]
    ) -> List[NetworkInterface]:
        """Discover network interface information."""
        ssh_runner = SSHCommandRunner(ssh_client)

        try:
            stdout, stderr, exit_code = ssh_runner.get_network_interfaces()
            if exit_code == 0:
                network_data = self.network_parser.parse_ip_addr(stdout)
                return network_data
            else:
                errors.append(f"Network interface discovery failed: {stderr}")

        except Exception as e:
            errors.append(f"Network discovery failed: {str(e)}")

        return []

    def _discover_vendor_info(
        self, ssh_client: SSHClient, system_info: SystemInfo, errors: List[str]
    ) -> Dict[str, Any]:
        """Discover vendor-specific information."""
        vendor_info: Dict[str, Any] = {}

        # Find appropriate vendor handler
        for vendor_class in self.vendor_handlers:
            try:
                vendor_handler = vendor_class(ssh_client)
                if vendor_handler.can_handle(system_info):
                    self.logger.info(f"Using {vendor_class.__name__} for discovery")
                    vendor_info = vendor_handler.discover_vendor_info(errors)
                    break
            except Exception as e:
                errors.append(f"Vendor discovery error ({vendor_class.__name__}): {e}")

        return vendor_info

    def _enhance_system_info(
        self, system_info: SystemInfo, vendor_info: Dict[str, Any]
    ):
        """Enhance system info with vendor-specific data."""
        # Update system info with vendor-specific details if available
        if "sum_product_name" in vendor_info:
            system_info.product_name = vendor_info["sum_product_name"]

        if "dell_service_tag" in vendor_info:
            system_info.serial_number = vendor_info["dell_service_tag"]

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        return datetime.now().isoformat()

    def find_ipmi_address(
        self, host: str, username: str = "ubuntu", key_file: str = None
    ) -> Optional[str]:
        """
        Quick method to find just the IPMI address.

        Args
        ----
        host : str
            Target hostname or IP address
        username : str, optional
            SSH username (default: ubuntu)
        key_file : str, optional
            SSH private key file path

        Returns
        -------
        str or None
            IPMI IP address if found, None otherwise
        """
        try:
            ssh_client = self.ssh_manager.connect(
                host=host, username=username, key_file=key_file, timeout=30
            )

            with ssh_client:
                errors: List[str] = []
                ipmi_info = self._discover_ipmi_info(ssh_client, errors)
                return ipmi_info.ip_address

        except Exception as e:
            self.logger.error(f"IPMI address discovery failed for {host}: {e}")
            return None
