"""
Hardware Discovery Module

This module provides tools for discovering hardware information from remote systems
via SSH, including IPMI addresses, system specifications, and network interfaces.
."""

import json
import logging
import re
from dataclasses import asdict, dataclass
from ipaddress import AddressValueError, IPv4Address
from typing import Any, Dict, List, Optional, Tuple

from ..logging import get_logger
from ..utils.network import SSHClient, SSHManager

logger = get_logger(__name__)


@dataclass
class NetworkInterface:
    """Network interface information."""

    name: str
    mac_address: str
    ip_address: Optional[str] = None
    netmask: Optional[str] = None
    state: str = "unknown"


@dataclass
class IPMIInfo:
    """IPMI configuration information."""

    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    gateway: Optional[str] = None
    netmask: Optional[str] = None
    vlan_id: Optional[int] = None
    channel: Optional[int] = None
    enabled: bool = False


@dataclass
class SystemInfo:
    """System hardware information."""

    manufacturer: Optional[str] = None
    product_name: Optional[str] = None
    serial_number: Optional[str] = None
    uuid: Optional[str] = None
    bios_version: Optional[str] = None
    bios_date: Optional[str] = None
    cpu_model: Optional[str] = None
    cpu_cores: Optional[int] = None
    memory_total: Optional[str] = None
    chassis_type: Optional[str] = None


@dataclass
class HardwareDiscovery:
    """Complete hardware discovery results."""

    hostname: str
    system_info: SystemInfo
    ipmi_info: IPMIInfo
    network_interfaces: List[NetworkInterface]
    discovered_at: str
    discovery_errors: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


class HardwareDiscoveryManager:
    """
    Manager for discovering hardware information from remote systems

    This class uses SSH to connect to systems and run discovery commands
    to gather hardware information including IPMI configuration.
    ."""

    def __init__(self, ssh_manager: SSHManager):
        """
        Initialize hardware discovery manager

        Args:
            ssh_manager: SSH manager for remote connections
        ."""
        self.ssh_manager = ssh_manager
        self.logger = get_logger(__name__)

    def discover_hardware(
        self, host: str, username: str = "ubuntu", key_file: str = None
    ) -> HardwareDiscovery:
        """
        Discover all hardware information from a remote system

        Args:
            host: Target hostname or IP address
            username: SSH username (default: ubuntu)
            key_file: SSH private key file path

        Returns:
            Complete hardware discovery results
        ."""
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

                return HardwareDiscovery(
                    hostname=host,
                    system_info=system_info,
                    ipmi_info=ipmi_info,
                    network_interfaces=network_interfaces,
                    discovered_at=self._get_timestamp(),
                    discovery_errors=errors,
                )

        except Exception as e:
            self.logger.error(f"Failed to discover hardware on {host}: {e}")
            errors.append(f"Connection failed: {str(e)}")

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
        """Discover system hardware information using dmidecode and vendor tools."""
        system_info = SystemInfo()

        try:
            # Get system information from dmidecode
            stdout, stderr, exit_code = ssh_client.exec_command(
                "sudo dmidecode -t system"
            )
            if exit_code == 0:
                system_info = self._parse_dmidecode_system(stdout)
            else:
                errors.append(f"dmidecode system failed: {stderr}")

            # Get BIOS information
            stdout, stderr, exit_code = ssh_client.exec_command(
                "sudo dmidecode -t bios"
            )
            if exit_code == 0:
                bios_info = self._parse_dmidecode_bios(stdout)
                system_info.bios_version = bios_info.get("version")
                system_info.bios_date = bios_info.get("date")
            else:
                errors.append(f"dmidecode bios failed: {stderr}")

            # Enhance with vendor-specific information
            if system_info.manufacturer:
                vendor_info = self._discover_vendor_specific_info(
                    ssh_client, system_info.manufacturer, errors
                )
                # Merge vendor-specific information
                if vendor_info:
                    for key, value in vendor_info.items():
                        if value and not getattr(system_info, key, None):
                            setattr(system_info, key, value)

            # Get CPU information
            stdout, stderr, exit_code = ssh_client.exec_command("lscpu")
            if exit_code == 0:
                cpu_info = self._parse_lscpu(stdout)
                system_info.cpu_model = cpu_info.get("model")
                system_info.cpu_cores = cpu_info.get("cores")
            else:
                errors.append(f"lscpu failed: {stderr}")

            # Get memory information
            stdout, stderr, exit_code = ssh_client.exec_command("free -h")
            if exit_code == 0:
                system_info.memory_total = self._parse_memory_info(stdout)
            else:
                errors.append(f"free command failed: {stderr}")

        except Exception as e:
            errors.append(f"System info discovery failed: {str(e)}")

        return system_info

    def _discover_ipmi_info(self, ssh_client: SSHClient, errors: List[str]) -> IPMIInfo:
        """Discover IPMI configuration information."""
        ipmi_info = IPMIInfo()

        try:
            # Check if ipmitool is available
            stdout, stderr, exit_code = ssh_client.exec_command("which ipmitool")
            if exit_code != 0:
                # Try to install ipmitool
                install_stdout, stderr, exit_code = ssh_client.exec_command(
                    "sudo apt-get update && sudo apt-get install -y ipmitool"
                )
                if exit_code != 0:
                    errors.append("ipmitool not available and installation failed")
                    return ipmi_info

            # Get IPMI LAN configuration
            stdout, stderr, exit_code = ssh_client.exec_command(
                "sudo ipmitool lan print 1"
            )
            if exit_code == 0:
                ipmi_info = self._parse_ipmi_lan_config(stdout)
                ipmi_info.enabled = True
                ipmi_info.channel = 1
            else:
                # Try channel 8 (common for some Dell systems)
                stdout, stderr, exit_code = ssh_client.exec_command(
                    "sudo ipmitool lan print 8"
                )
                if exit_code == 0:
                    ipmi_info = self._parse_ipmi_lan_config(stdout)
                    ipmi_info.enabled = True
                    ipmi_info.channel = 8
                else:
                    errors.append("IPMI LAN configuration not accessible")

        except Exception as e:
            errors.append(f"IPMI discovery failed: {str(e)}")

        return ipmi_info

    def _discover_vendor_specific_info(
        self, ssh_client: SSHClient, manufacturer: str, errors: List[str]
    ) -> Dict[str, Any]:
        """Discover vendor-specific hardware information."""
        vendor_info = {}

        try:
            manufacturer_lower = manufacturer.lower()

            if (
                "supermicro" in manufacturer_lower
                or "super micro" in manufacturer_lower
            ):
                vendor_info.update(self._discover_supermicro_info(ssh_client, errors))
            elif (
                "hewlett" in manufacturer_lower
                or "hpe" in manufacturer_lower
                or "hp " in manufacturer_lower
            ):
                vendor_info.update(self._discover_hpe_info(ssh_client, errors))
            elif "dell" in manufacturer_lower:
                vendor_info.update(self._discover_dell_info(ssh_client, errors))

        except Exception as e:
            errors.append(f"Vendor-specific discovery failed: {str(e)}")

        return vendor_info

    def _discover_supermicro_info(
        self, ssh_client: SSHClient, errors: List[str]
    ) -> Dict[str, Any]:
        """Discover Supermicro-specific information using sumtool."""
        supermicro_info: Dict[str, Any] = {}

        try:
            # Check if sumtool is available
            stdout, stderr, exit_code = ssh_client.exec_command("which sumtool")
            if exit_code != 0:
                # Try to install sumtool
                self.logger.info("Installing Supermicro sumtool...")
                install_result = self._install_sumtool(ssh_client, errors)
                if not install_result:
                    return supermicro_info

            # Get system information using sumtool
            stdout, stderr, exit_code = ssh_client.exec_command(
                "sudo sumtool -c GetSystemInfo"
            )
            if exit_code == 0:
                sumtool_info = self._parse_sumtool_system_info(stdout)
                supermicro_info.update(sumtool_info)
            else:
                errors.append(f"sumtool GetSystemInfo failed: {stderr}")

            # Get BIOS information using sumtool
            stdout, stderr, exit_code = ssh_client.exec_command(
                "sudo sumtool -c GetBiosInfo"
            )
            if exit_code == 0:
                bios_info = self._parse_sumtool_bios_info(stdout)
                supermicro_info.update(bios_info)
            else:
                errors.append(f"sumtool GetBiosInfo failed: {stderr}")

            # Get BMC/IPMI information using sumtool
            stdout, stderr, exit_code = ssh_client.exec_command(
                "sudo sumtool -c GetBmcInfo"
            )
            if exit_code == 0:
                bmc_info = self._parse_sumtool_bmc_info(stdout)
                supermicro_info.update(bmc_info)
            else:
                errors.append(f"sumtool GetBmcInfo failed: {stderr}")

        except Exception as e:
            errors.append(f"Supermicro discovery failed: {str(e)}")

        return supermicro_info

    def _discover_hpe_info(
        self, ssh_client: SSHClient, errors: List[str]
    ) -> Dict[str, Any]:
        """Discover HPE-specific information using hpssacli or ssacli."""
        hpe_info = {}

        try:
            # Check for HPE tools (hpssacli or ssacli)
            hpe_tool = None
            for tool in ["hpssacli", "ssacli"]:
                stdout, stderr, exit_code = ssh_client.exec_command(f"which {tool}")
                if exit_code == 0:
                    hpe_tool = tool
                    break

            if not hpe_tool:
                # Try to install HPE tools
                self.logger.info("Installing HPE management tools...")
                install_result = self._install_hpe_tools(ssh_client, errors)
                if install_result:
                    hpe_tool = "hpssacli"  # Default after installation

            # Get system information using HPE tools
            if hpe_tool:
                stdout, stderr, exit_code = ssh_client.exec_command(
                    f"sudo {hpe_tool} ctrl all show config"
                )
                if exit_code == 0:
                    hpe_controller_info = self._parse_hpe_controller_info(stdout)
                    hpe_info.update(hpe_controller_info)
                else:
                    errors.append(f"{hpe_tool} controller query failed: {stderr}")

            # Check for HPE iLO information
            stdout, stderr, exit_code = ssh_client.exec_command(
                "sudo dmidecode -t 38 | grep -i ilo"
            )
            if exit_code == 0 and stdout.strip():
                hpe_info["ilo_present"] = True

        except Exception as e:
            errors.append(f"HPE discovery failed: {str(e)}")

        return hpe_info

    def _discover_dell_info(
        self, ssh_client: SSHClient, errors: List[str]
    ) -> Dict[str, Any]:
        """Discover Dell-specific information using omreport."""
        dell_info: Dict[str, Any] = {}

        try:
            # Check for Dell OpenManage tools
            stdout, stderr, exit_code = ssh_client.exec_command("which omreport")
            if exit_code != 0:
                # Try to install Dell OpenManage tools
                self.logger.info("Installing Dell OpenManage tools...")
                install_result = self._install_dell_tools(ssh_client, errors)
                if not install_result:
                    return dell_info

            # Get chassis information
            stdout, stderr, exit_code = ssh_client.exec_command(
                "sudo omreport chassis info"
            )
            if exit_code == 0:
                dell_chassis_info = self._parse_dell_chassis_info(stdout)
                dell_info.update(dell_chassis_info)
            else:
                errors.append(f"omreport chassis failed: {stderr}")

        except Exception as e:
            errors.append(f"Dell discovery failed: {str(e)}")

        return dell_info

    def _install_sumtool(self, ssh_client: SSHClient, errors: List[str]) -> bool:
        """Install Supermicro sumtool."""
        try:
            # Check if sumtool is already installed
            stdout, stderr, exit_code = ssh_client.exec_command("which sumtool")
            if exit_code == 0:
                self.logger.info("sumtool already installed")
                return True

            # Update package lists
            stdout, stderr, exit_code = ssh_client.exec_command("sudo apt-get update")
            if exit_code != 0:
                errors.append("Failed to update package lists")
                return False

            # Install dependencies
            stdout, stderr, exit_code = ssh_client.exec_command(
                "sudo apt-get install -y wget alien"
            )
            if exit_code != 0:
                errors.append("Failed to install dependencies for sumtool")
                return False

            # Download and install sumtool
            commands = [
                "cd /tmp",
                "wget -q https://www.supermicro.com/SwDownload/SwSelect/25/sum_2.11.0_Linux_x86_64_20230825.tar.gz -O sumtool.tar.gz",
                "tar -xzf sumtool.tar.gz",
                "cd sum_*",
                "sudo cp sum /usr/local/bin/sumtool",  # Install as sumtool, not sum
                "sudo chmod +x /usr/local/bin/sumtool",
                "sudo ln -sf /usr/local/bin/sumtool /usr/bin/sumtool",  # Create symlink as sumtool
            ]

            for cmd in commands:
                stdout, stderr, exit_code = ssh_client.exec_command(cmd)
                if exit_code != 0:
                    errors.append(f"sumtool installation step failed: {cmd}")
                    return False

            # Verify installation
            stdout, stderr, exit_code = ssh_client.exec_command("sumtool --version")
            if exit_code == 0:
                self.logger.info("sumtool installed successfully")
                return True
            else:
                errors.append("sumtool installation verification failed")
                return False

        except Exception as e:
            errors.append(f"sumtool installation failed: {str(e)}")
            return False

    def _install_hpe_tools(self, ssh_client: SSHClient, errors: List[str]) -> bool:
        """Install HPE management tools."""
        try:
            # Update package lists
            stdout, stderr, exit_code = ssh_client.exec_command("sudo apt-get update")
            if exit_code != 0:
                errors.append("Failed to update package lists")
                return False

            # Install HPE repository and tools
            commands = [
                "wget -q https://downloads.linux.hpe.com/SDR/hpPublicKey2048_key1.pub -O /tmp/hpPublicKey2048_key1.pub",
                "sudo apt-key add /tmp/hpPublicKey2048_key1.pub",
                "echo 'deb http://downloads.linux.hpe.com/SDR/repo/mcp $(lsb_release -sc)/current non-free' | sudo tee /etc/apt/sources.list.d/hpe-mcp.list",
                "sudo apt-get update",
                "sudo apt-get install -y hpssacli",
            ]

            for cmd in commands:
                stdout, stderr, exit_code = ssh_client.exec_command(cmd)
                if exit_code != 0:
                    self.logger.warning(f"HPE tools installation step failed: {cmd}")
                    # Continue with next command as some may be optional

            # Verify installation
            stdout, stderr, exit_code = ssh_client.exec_command("which hpssacli")
            if exit_code == 0:
                self.logger.info("HPE tools installed successfully")
                return True
            else:
                errors.append("HPE tools installation verification failed")
                return False

        except Exception as e:
            errors.append(f"HPE tools installation failed: {str(e)}")
            return False

    def _install_dell_tools(self, ssh_client: SSHClient, errors: List[str]) -> bool:
        """Install Dell OpenManage tools."""
        try:
            # Update package lists
            stdout, stderr, exit_code = ssh_client.exec_command("sudo apt-get update")
            if exit_code != 0:
                errors.append("Failed to update package lists")
                return False

            # Install Dell repository and OpenManage
            commands = [
                "wget -q -O - https://linux.dell.com/repo/hardware/dsu/public.key | sudo apt-key add -",
                "echo 'deb http://linux.dell.com/repo/hardware/dsu/os_independent/ /' | sudo tee /etc/apt/sources.list.d/dell-system-update.list",
                "sudo apt-get update",
                "sudo apt-get install -y srvadmin-base srvadmin-storageservices",
            ]

            for cmd in commands:
                stdout, stderr, exit_code = ssh_client.exec_command(cmd)
                if exit_code != 0:
                    self.logger.warning(f"Dell tools installation step failed: {cmd}")
                    # Continue with next command as some may be optional

            # Start services
            ssh_client.exec_command(
                "sudo /opt/dell/srvadmin/sbin/srvadmin-services.sh start"
            )

            # Verify installation
            stdout, stderr, exit_code = ssh_client.exec_command("which omreport")
            if exit_code == 0:
                self.logger.info("Dell OpenManage tools installed successfully")
                return True
            else:
                errors.append("Dell tools installation verification failed")
                return False

        except Exception as e:
            errors.append(f"Dell tools installation failed: {str(e)}")
            return False

    def _parse_sumtool_system_info(self, output: str) -> Dict[str, Any]:
        """Parse sumtool system information output."""
        info = {}

        for line in output.split("\n"):
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()

                if "product name" in key:
                    info["product_name"] = value
                elif "serial number" in key:
                    info["serial_number"] = value
                elif "manufacturer" in key:
                    info["manufacturer"] = value
                elif "system uuid" in key or "uuid" in key:
                    info["uuid"] = value

        return info

    def _parse_sumtool_bios_info(self, output: str) -> Dict[str, Any]:
        """Parse sumtool BIOS information output."""
        info = {}

        for line in output.split("\n"):
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()

                if "bios version" in key or "version" in key:
                    info["bios_version"] = value
                elif "bios date" in key or "release date" in key:
                    info["bios_date"] = value

        return info

    def _parse_sumtool_bmc_info(self, output: str) -> Dict[str, Any]:
        """Parse sumtool BMC information output."""
        info = {}

        for line in output.split("\n"):
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()

                if "bmc version" in key or "firmware version" in key:
                    info["bmc_version"] = value
                elif "bmc ip" in key or "ip address" in key:
                    info["bmc_ip"] = value

        return info

    def _parse_hpe_controller_info(self, output: str) -> Dict[str, Any]:
        """Parse HPE controller information output."""
        info = {}
        controllers = []

        current_controller = None

        for line in output.split("\n"):
            line = line.strip()

            if "Smart Array" in line:
                if current_controller:
                    controllers.append(current_controller)
                current_controller = {"model": line}
            elif current_controller and ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()

                if "serial number" in key:
                    current_controller["serial"] = value
                elif "firmware version" in key:
                    current_controller["firmware"] = value

        if current_controller:
            controllers.append(current_controller)

        if controllers:
            info["storage_controllers"] = controllers

        return info

    def _parse_dell_chassis_info(self, output: str) -> Dict[str, Any]:
        """Parse Dell chassis information output."""
        info = {}

        for line in output.split("\n"):
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()

                if "chassis model" in key:
                    info["chassis_model"] = value
                elif "service tag" in key:
                    info["service_tag"] = value
                elif "express service code" in key:
                    info["express_service_code"] = value

        return info

    def _discover_network_interfaces(
        self, ssh_client: SSHClient, errors: List[str]
    ) -> List[NetworkInterface]:
        """Discover network interface information."""
        interfaces = []

        try:
            # Get interface information using ip command
            stdout, stderr, exit_code = ssh_client.exec_command("ip addr show")
            if exit_code == 0:
                interfaces = self._parse_ip_addr(stdout)
            else:
                errors.append(f"ip addr command failed: {stderr}")

        except Exception as e:
            errors.append(f"Network interface discovery failed: {str(e)}")

        return interfaces

    def _parse_dmidecode_system(self, output: str) -> SystemInfo:
        """Parse dmidecode system output."""
        system_info = SystemInfo()

        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("Manufacturer:"):
                system_info.manufacturer = line.split(":", 1)[1].strip()
            elif line.startswith("Product Name:"):
                system_info.product_name = line.split(":", 1)[1].strip()
            elif line.startswith("Serial Number:"):
                system_info.serial_number = line.split(":", 1)[1].strip()
            elif line.startswith("UUID:"):
                system_info.uuid = line.split(":", 1)[1].strip()

        return system_info

    def _parse_dmidecode_bios(self, output: str) -> Dict[str, str]:
        """Parse dmidecode BIOS output."""
        bios_info = {}

        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("Version:"):
                bios_info["version"] = line.split(":", 1)[1].strip()
            elif line.startswith("Release Date:"):
                bios_info["date"] = line.split(":", 1)[1].strip()

        return bios_info

    def _parse_lscpu(self, output: str) -> Dict[str, Any]:
        """Parse lscpu output."""
        cpu_info: Dict[str, Any] = {}

        for line in output.split("\n"):
            line = line.strip()
            if line.startswith("Model name:"):
                cpu_info["model"] = line.split(":", 1)[1].strip()
            elif line.startswith("CPU(s):"):
                try:
                    cpu_info["cores"] = int(line.split(":", 1)[1].strip())
                except ValueError:
                    pass

        return cpu_info

    def _parse_memory_info(self, output: str) -> Optional[str]:
        """Parse free command output for total memory."""
        for line in output.split("\n"):
            if line.startswith("Mem:"):
                parts = line.split()
                if len(parts) >= 2:
                    return parts[1]  # Total memory
        return None

    def _parse_ipmi_lan_config(self, output: str) -> IPMIInfo:
        """Parse ipmitool lan print output."""
        ipmi_info = IPMIInfo()

        for line in output.split("\n"):
            line = line.strip()
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                if key == "IP Address":
                    ipmi_info.ip_address = value if value != "0.0.0.0" else None
                elif key == "MAC Address":
                    ipmi_info.mac_address = value
                elif key == "Default Gateway IP":
                    ipmi_info.gateway = value if value != "0.0.0.0" else None
                elif key == "Subnet Mask":
                    ipmi_info.netmask = value if value != "0.0.0.0" else None
                elif key == "802.1q VLAN ID":
                    try:
                        if value.lower() != "disabled":
                            ipmi_info.vlan_id = int(value)
                    except ValueError:
                        pass

        return ipmi_info

    def _parse_ip_addr(self, output: str) -> List[NetworkInterface]:
        """Parse ip addr show output."""
        interfaces = []
        current_interface = None

        for line in output.split("\n"):
            line = line.strip()

            # Interface line (e.g., "2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500")
            if re.match(r"^\d+:", line):
                if current_interface:
                    interfaces.append(current_interface)

                parts = line.split()
                if len(parts) >= 2:
                    name = parts[1].rstrip(":")
                    state = "up" if "UP" in line else "down"
                    current_interface = NetworkInterface(
                        name=name, mac_address="", state=state
                    )

            # MAC address line (e.g., "link/ether 00:50:56:xx:xx:xx brd ff:ff:ff:ff:ff:ff")
            elif line.startswith("link/ether") and current_interface:
                parts = line.split()
                if len(parts) >= 2:
                    current_interface.mac_address = parts[1]

            # IP address line (e.g., "inet 192.168.1.100/24 brd 192.168.1.255 scope global eth0")
            elif line.startswith("inet ") and current_interface:
                parts = line.split()
                if len(parts) >= 2:
                    ip_cidr = parts[1]
                    if "/" in ip_cidr:
                        ip, cidr = ip_cidr.split("/")
                        current_interface.ip_address = ip
                        current_interface.netmask = self._cidr_to_netmask(int(cidr))

        # Add the last interface
        if current_interface:
            interfaces.append(current_interface)

        return interfaces

    def _cidr_to_netmask(self, cidr: int) -> str:
        """Convert CIDR notation to netmask."""
        mask = (0xFFFFFFFF >> (32 - cidr)) << (32 - cidr)
        return f"{(mask >> 24) & 0xff}.{(mask >> 16) & 0xff}.{(mask >> 8) & 0xff}.{mask & 0xff}"

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime

        return datetime.now().isoformat()

    def find_ipmi_address(
        self, host: str, username: str = "ubuntu", key_file: str = None
    ) -> Optional[str]:
        """
        Quick method to find just the IPMI address

        Args:
            host: Target hostname or IP address
            username: SSH username
            key_file: SSH private key file path

        Returns:
            IPMI IP address if found, None otherwise
        ."""
        try:
            discovery = self.discover_hardware(host, username, key_file)
            return discovery.ipmi_info.ip_address
        except Exception as e:
            self.logger.error(f"Failed to find IPMI address for {host}: {e}")
            return None

    def discover_ipmi_from_network_scan(self, network_range: str) -> Dict[str, str]:
        """
        Discover IPMI addresses by scanning a network range

        Args:
            network_range: Network range to scan (e.g., "192.168.1.0/24")

        Returns:
            Dictionary mapping hostnames to IPMI addresses
        """
        ipmi_addresses = {}

        try:
            from ipaddress import IPv4Network

            network = IPv4Network(network_range, strict=False)

            self.logger.info(f"Scanning network {network_range} for IPMI addresses")

            for ip in network.hosts():
                ip_str = str(ip)

                # Try to connect and discover IPMI
                try:
                    ipmi_addr = self.find_ipmi_address(ip_str)
                    if ipmi_addr:
                        ipmi_addresses[ip_str] = ipmi_addr
                        self.logger.info(
                            f"Found IPMI address {ipmi_addr} for host {ip_str}"
                        )
                except Exception as e:
                    self.logger.debug(f"Could not discover IPMI for {ip_str}: {e}")

        except Exception as e:
            self.logger.error(f"Network scan failed: {e}")

        return ipmi_addresses
