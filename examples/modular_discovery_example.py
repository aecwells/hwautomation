"""
Example: Hardware Discovery Module Refactoring

This shows how to refactor the large discovery.py file into modular components.
"""

# src/hwautomation/hardware/discovery/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ...utils.network import SSHClient


@dataclass
class VendorInfo:
    """Vendor-specific hardware information."""
    vendor: str
    tools_installed: List[str] = None
    additional_info: Dict[str, Any] = None


class BaseVendorDiscovery(ABC):
    """Base class for vendor-specific hardware discovery."""
    
    @property
    @abstractmethod
    def vendor_name(self) -> str:
        """Return the vendor name this discovery module handles."""
        pass
    
    @property
    @abstractmethod
    def required_tools(self) -> List[str]:
        """Return list of tools required for this vendor."""
        pass
    
    @abstractmethod
    def detect_vendor(self, system_info: Dict[str, Any]) -> bool:
        """Detect if this system matches the vendor."""
        pass
    
    @abstractmethod
    def install_tools(self, ssh_client: SSHClient) -> bool:
        """Install vendor-specific tools."""
        pass
    
    @abstractmethod
    def discover_info(self, ssh_client: SSHClient) -> VendorInfo:
        """Discover vendor-specific information."""
        pass


# src/hwautomation/hardware/discovery/vendors/supermicro.py
import logging
from typing import Any, Dict, List

from ..base import BaseVendorDiscovery, VendorInfo
from ....utils.network import SSHClient

logger = logging.getLogger(__name__)


class SupermicroDiscovery(BaseVendorDiscovery):
    """Supermicro-specific hardware discovery."""
    
    @property
    def vendor_name(self) -> str:
        return "Supermicro"
    
    @property
    def required_tools(self) -> List[str]:
        return ["sumtool"]
    
    def detect_vendor(self, system_info: Dict[str, Any]) -> bool:
        """Detect if this is a Supermicro system."""
        manufacturer = system_info.get("manufacturer", "").lower()
        return "supermicro" in manufacturer or "super micro" in manufacturer
    
    def install_tools(self, ssh_client: SSHClient) -> bool:
        """Install Supermicro sumtool."""
        try:
            # Check if already installed
            stdout, stderr, exit_code = ssh_client.exec_command("which sumtool")
            if exit_code == 0:
                logger.debug("sumtool already installed")
                return True
            
            # Install sumtool
            install_commands = [
                "wget -q http://repo.supermicro.com/SUM/sum_2.12.0_Linux_x86_64_20240115.tar.gz",
                "tar -xzf sum_2.12.0_Linux_x86_64_20240115.tar.gz",
                "sudo ./sum_2.12.0_Linux_x86_64/install.sh -s",
                "rm -rf sum_2.12.0_Linux_x86_64*"
            ]
            
            for cmd in install_commands:
                stdout, stderr, exit_code = ssh_client.exec_command(cmd)
                if exit_code != 0:
                    logger.error(f"Failed to install sumtool: {stderr}")
                    return False
            
            logger.info("Successfully installed sumtool")
            return True
            
        except Exception as e:
            logger.error(f"Exception installing sumtool: {e}")
            return False
    
    def discover_info(self, ssh_client: SSHClient) -> VendorInfo:
        """Discover Supermicro-specific information."""
        vendor_info = VendorInfo(vendor=self.vendor_name, additional_info={})
        
        try:
            # Get system information
            stdout, stderr, exit_code = ssh_client.exec_command("sumtool -c GetSystemInfo")
            if exit_code == 0:
                system_info = self._parse_sumtool_system_info(stdout)
                vendor_info.additional_info.update(system_info)
            
            # Get BIOS information
            stdout, stderr, exit_code = ssh_client.exec_command("sumtool -c GetBiosInfo")
            if exit_code == 0:
                bios_info = self._parse_sumtool_bios_info(stdout)
                vendor_info.additional_info.update(bios_info)
            
            # Get BMC information
            stdout, stderr, exit_code = ssh_client.exec_command("sumtool -c GetBmcInfo")
            if exit_code == 0:
                bmc_info = self._parse_sumtool_bmc_info(stdout)
                vendor_info.additional_info.update(bmc_info)
            
            vendor_info.tools_installed = ["sumtool"]
            
        except Exception as e:
            logger.error(f"Failed to discover Supermicro info: {e}")
        
        return vendor_info
    
    def _parse_sumtool_system_info(self, output: str) -> Dict[str, Any]:
        """Parse sumtool system information output."""
        info = {}
        # Implementation for parsing sumtool output
        # ... parsing logic here ...
        return info
    
    def _parse_sumtool_bios_info(self, output: str) -> Dict[str, Any]:
        """Parse sumtool BIOS information output."""
        info = {}
        # Implementation for parsing BIOS info
        # ... parsing logic here ...
        return info
    
    def _parse_sumtool_bmc_info(self, output: str) -> Dict[str, Any]:
        """Parse sumtool BMC information output."""
        info = {}
        # Implementation for parsing BMC info
        # ... parsing logic here ...
        return info


# src/hwautomation/hardware/discovery/manager.py
import logging
from typing import Dict, List, Optional, Type

from .base import BaseVendorDiscovery
from .vendors.supermicro import SupermicroDiscovery
from .vendors.hpe import HPEDiscovery
from .vendors.dell import DellDiscovery
from ..data_models import HardwareDiscovery, SystemInfo
from ...utils.network import SSHClient

logger = logging.getLogger(__name__)


class VendorDiscoveryRegistry:
    """Registry for vendor discovery implementations."""
    
    def __init__(self):
        self._vendors: Dict[str, Type[BaseVendorDiscovery]] = {}
        self._register_default_vendors()
    
    def _register_default_vendors(self):
        """Register built-in vendor discovery implementations."""
        self.register(SupermicroDiscovery)
        self.register(HPEDiscovery)
        self.register(DellDiscovery)
    
    def register(self, vendor_class: Type[BaseVendorDiscovery]):
        """Register a vendor discovery implementation."""
        instance = vendor_class()
        self._vendors[instance.vendor_name.lower()] = vendor_class
        logger.debug(f"Registered vendor discovery: {instance.vendor_name}")
    
    def get_vendor_discovery(self, vendor_name: str) -> Optional[BaseVendorDiscovery]:
        """Get vendor discovery instance by name."""
        vendor_class = self._vendors.get(vendor_name.lower())
        return vendor_class() if vendor_class else None
    
    def detect_vendor(self, system_info: Dict) -> Optional[BaseVendorDiscovery]:
        """Auto-detect vendor based on system information."""
        for vendor_class in self._vendors.values():
            vendor_instance = vendor_class()
            if vendor_instance.detect_vendor(system_info):
                return vendor_instance
        return None


class ModularHardwareDiscoveryManager:
    """Modular hardware discovery manager with plugin architecture."""
    
    def __init__(self, ssh_manager, config: Dict = None):
        self.ssh_manager = ssh_manager
        self.config = config or {}
        self.vendor_registry = VendorDiscoveryRegistry()
        self.logger = logging.getLogger(__name__)
    
    def discover_hardware(
        self, 
        hostname: str, 
        username: str = "ubuntu", 
        ssh_key_path: str = None
    ) -> HardwareDiscovery:
        """
        Discover hardware information using modular vendor-specific plugins.
        """
        errors = []
        
        try:
            # Establish SSH connection
            ssh_client = self.ssh_manager.get_client(
                hostname=hostname,
                username=username,
                key_filename=ssh_key_path
            )
            
            # Discover basic system information
            system_info = self._discover_system_info(ssh_client, errors)
            
            # Auto-detect and run vendor-specific discovery
            vendor_discovery = self.vendor_registry.detect_vendor(
                {"manufacturer": system_info.manufacturer}
            )
            
            if vendor_discovery:
                self.logger.info(f"Detected vendor: {vendor_discovery.vendor_name}")
                
                # Install vendor tools if needed
                if not self._ensure_vendor_tools(ssh_client, vendor_discovery):
                    errors.append(f"Failed to install {vendor_discovery.vendor_name} tools")
                else:
                    # Run vendor-specific discovery
                    vendor_info = vendor_discovery.discover_info(ssh_client)
                    
                    # Merge vendor information into system info
                    if vendor_info.additional_info:
                        for key, value in vendor_info.additional_info.items():
                            if value and not getattr(system_info, key, None):
                                setattr(system_info, key, value)
            
            # Discover other information (IPMI, network interfaces, etc.)
            ipmi_info = self._discover_ipmi_info(ssh_client, errors)
            network_interfaces = self._discover_network_interfaces(ssh_client, errors)
            
            return HardwareDiscovery(
                hostname=hostname,
                system_info=system_info,
                ipmi_info=ipmi_info,
                network_interfaces=network_interfaces,
                discovered_at=self._get_timestamp(),
                discovery_errors=errors,
            )
            
        except Exception as e:
            self.logger.error(f"Failed to discover hardware on {hostname}: {e}")
            errors.append(f"Connection failed: {str(e)}")
            
            return HardwareDiscovery(
                hostname=hostname,
                system_info=SystemInfo(),
                ipmi_info=None,
                network_interfaces=[],
                discovered_at=self._get_timestamp(),
                discovery_errors=errors,
            )
    
    def _ensure_vendor_tools(
        self, 
        ssh_client: SSHClient, 
        vendor_discovery: BaseVendorDiscovery
    ) -> bool:
        """Ensure vendor-specific tools are installed."""
        try:
            return vendor_discovery.install_tools(ssh_client)
        except Exception as e:
            self.logger.error(f"Failed to install vendor tools: {e}")
            return False
    
    # ... other existing methods would be moved here from the original discovery.py
    # _discover_system_info, _discover_ipmi_info, etc.


# Usage example in updated code:
def create_discovery_manager(ssh_manager, config=None):
    """Factory function for creating discovery manager."""
    return ModularHardwareDiscoveryManager(ssh_manager, config)
