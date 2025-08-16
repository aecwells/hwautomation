"""Base classes and data structures for hardware discovery.

This module contains the core data structures and abstract base classes
used throughout the hardware discovery system.
"""

import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

from ...logging import get_logger

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

    # Enhanced fields for device classification
    device_type: Optional[str] = None
    classification_confidence: Optional[str] = None
    matching_criteria: Optional[List[str]] = None


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


class BaseVendorDiscovery(ABC):
    """Abstract base class for vendor-specific hardware discovery."""

    def __init__(self, ssh_client):
        """Initialize vendor discovery with SSH client."""
        self.ssh_client = ssh_client
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def can_handle(self, system_info: SystemInfo) -> bool:
        """Check if this vendor handler can process the given system."""
        pass

    @abstractmethod
    def get_vendor_specific_info(self, system_info: SystemInfo) -> Dict[str, Any]:
        """Get vendor-specific hardware information."""
        pass

    @abstractmethod
    def install_vendor_tools(self) -> bool:
        """Install vendor-specific discovery tools if needed."""
        pass

    def get_priority(self) -> int:
        """Get priority for vendor selection (lower = higher priority)."""
        return 100  # Default priority


class BaseParser(ABC):
    """Abstract base class for output parsers."""

    def __init__(self):
        """Initialize parser."""
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def parse(self, output: str) -> Dict[str, Any]:
        """Parse command output and return structured data."""
        pass

    def safe_parse(self, output: str) -> Dict[str, Any]:
        """Safely parse output with error handling."""
        try:
            return self.parse(output)
        except Exception as e:
            self.logger.warning(f"Failed to parse output: {e}")
            return {}
