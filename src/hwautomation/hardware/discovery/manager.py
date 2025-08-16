"""Main hardware discovery manager module.

This module coordinates the hardware discovery process using
various parsers and vendor-specific handlers, with enhanced
device classification through unified configuration integration.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Type

from ...config.adapters import ConfigurationManager
from ...config.unified_loader import UnifiedConfigLoader
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
    and vendor-specific handlers for comprehensive hardware information,
    with enhanced device classification through unified configuration.
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

        # Initialize unified configuration system
        self.config_manager = ConfigurationManager()
        self.unified_loader = self.config_manager.get_unified_loader()

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

        # Check which configuration system we're using
        config_source = "unified" if self.unified_loader else "legacy"
        self.logger.info(
            f"Initialized HardwareDiscoveryManager with {config_source} configuration"
        )

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

                # Perform device classification using unified configuration
                self._classify_and_enhance_system_info(system_info)

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

    def _classify_and_enhance_system_info(self, system_info: SystemInfo):
        """Classify device type and enhance system info with classification results."""
        try:
            classification = self.classify_device_type(system_info)

            # Update system info with classification results
            system_info.device_type = classification.get("device_type")
            system_info.classification_confidence = classification.get("confidence")
            system_info.matching_criteria = classification.get("matching_criteria", [])

            if classification.get("device_type") != "unknown":
                self.logger.info(
                    f"Classified system as '{classification['device_type']}' "
                    f"with {classification['confidence']} confidence "
                    f"(criteria: {', '.join(classification.get('matching_criteria', []))})"
                )
            else:
                self.logger.warning(
                    "Could not classify device type from discovered hardware"
                )

        except Exception as e:
            self.logger.error(f"Device classification failed: {e}")
            system_info.device_type = "unknown"
            system_info.classification_confidence = "error"
            system_info.matching_criteria = []

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

    # Enhanced methods using unified configuration

    def classify_device_type(self, system_info: SystemInfo) -> Dict[str, Any]:
        """
        Classify device type based on system information using unified configuration.

        Args:
            system_info: System hardware information

        Returns:
            Dictionary with device classification results
        """
        if not self.unified_loader:
            return {
                "device_type": "unknown",
                "confidence": "low",
                "matching_criteria": [],
                "source": "legacy",
            }

        try:
            # Get all device types from unified config for comparison
            all_device_types = self.unified_loader.list_all_device_types()
            best_match = None
            best_score = 0
            matching_criteria = []

            for device_type in all_device_types:
                device_info = self.unified_loader.get_device_by_type(device_type)
                if not device_info:
                    continue

                score, criteria = self._calculate_match_score(system_info, device_info)

                if score > best_score:
                    best_score = score
                    best_match = device_type
                    matching_criteria = criteria

            # Determine confidence level
            if best_score >= 0.8:
                confidence = "high"
            elif best_score >= 0.5:
                confidence = "medium"
            elif best_score >= 0.3:
                confidence = "low"
            else:
                confidence = "very_low"

            return {
                "device_type": best_match or "unknown",
                "confidence": confidence,
                "score": best_score,
                "matching_criteria": matching_criteria,
                "source": "unified",
            }

        except Exception as e:
            self.logger.error(f"Device classification failed: {e}")
            return {
                "device_type": "unknown",
                "confidence": "error",
                "matching_criteria": [],
                "source": "error",
                "error": str(e),
            }

    def _calculate_match_score(self, system_info: SystemInfo, device_info) -> tuple:
        """
        Calculate match score between system info and device config.

        Returns:
            Tuple of (score, matching_criteria)
        """
        score = 0.0
        criteria = []

        # Check vendor/manufacturer match (high weight)
        if (
            system_info.manufacturer
            and system_info.manufacturer.lower() == device_info.vendor.lower()
        ):
            score += 0.4
            criteria.append("vendor_match")

        # Check motherboard/product name match (high weight)
        if (
            system_info.product_name
            and device_info.motherboard.lower() in system_info.product_name.lower()
        ):
            score += 0.3
            criteria.append("motherboard_match")

        # Check CPU model match (medium weight)
        device_config = device_info.device_config
        expected_cpu = device_config.get("cpu_name", "")
        if (
            system_info.cpu_model
            and expected_cpu
            and any(
                cpu_part in system_info.cpu_model for cpu_part in expected_cpu.split()
            )
        ):
            score += 0.2
            criteria.append("cpu_match")

        # Check CPU cores match (low weight)
        expected_cores = device_config.get("cpu_cores", 0)
        if (
            system_info.cpu_cores
            and expected_cores
            and system_info.cpu_cores == expected_cores
        ):
            score += 0.1
            criteria.append("cpu_cores_match")

        return score, criteria

    def get_supported_vendors(self) -> Dict[str, Any]:
        """Get supported vendors with device counts."""
        if self.unified_loader:
            vendors = {}
            for vendor_name in self.unified_loader.list_vendors():
                device_types = self.unified_loader.get_device_types_by_vendor(
                    vendor_name
                )
                motherboards = self.unified_loader.list_motherboards(vendor_name)
                vendors[vendor_name] = {
                    "device_count": len(device_types),
                    "motherboard_count": len(motherboards),
                    "device_types": device_types,
                    "motherboards": motherboards,
                }
            return vendors
        else:
            # Fallback for legacy configuration
            return {
                "supermicro": {"device_count": 3, "motherboard_count": 1},
                "hpe": {"device_count": 1, "motherboard_count": 1},
            }

    def get_motherboard_mapping(self) -> Dict[str, List[str]]:
        """Get mapping of motherboards to device types."""
        if self.unified_loader:
            mapping = {}
            for vendor_name in self.unified_loader.list_vendors():
                motherboards = self.unified_loader.list_motherboards(vendor_name)
                for motherboard in motherboards:
                    device_types = self.unified_loader.get_device_types_by_motherboard(
                        motherboard
                    )
                    mapping[motherboard] = device_types
            return mapping
        else:
            # Fallback mapping
            return {
                "X11DPT-B": ["flex-*.c.large"],
                "ProLiant RL300 Gen11": ["a1.c5.large"],
            }

    def search_device_types(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for device types matching a term."""
        if self.unified_loader:
            matching_devices = []
            all_device_types = self.unified_loader.list_all_device_types()

            for device_type in all_device_types:
                device_info = self.unified_loader.get_device_by_type(device_type)
                if device_info:
                    # Check if search term matches any field
                    search_lower = search_term.lower()
                    device_config = device_info.device_config

                    if (
                        search_lower in device_type.lower()
                        or search_lower in device_info.vendor.lower()
                        or search_lower in device_info.motherboard.lower()
                        or search_lower in device_config.get("cpu_name", "").lower()
                    ):

                        matching_devices.append(
                            {
                                "device_type": device_type,
                                "vendor": device_info.vendor,
                                "motherboard": device_info.motherboard,
                                "cpu_name": device_config.get("cpu_name", "Unknown"),
                                "cpu_cores": device_config.get("cpu_cores", 0),
                                "ram_gb": device_config.get("ram_gb", 0),
                            }
                        )

            return matching_devices
        else:
            # Simple fallback search
            return []

    def get_configuration_status(self) -> Dict[str, Any]:
        """Get configuration system status."""
        return {
            "unified_config_available": self.unified_loader is not None,
            "config_source": "unified" if self.unified_loader else "legacy",
            "supported_device_count": (
                len(self.unified_loader.list_all_device_types())
                if self.unified_loader
                else 4
            ),
            "vendor_count": (
                len(self.unified_loader.list_vendors()) if self.unified_loader else 2
            ),
            "adapters_status": (
                self.config_manager.get_status() if self.unified_loader else None
            ),
        }
