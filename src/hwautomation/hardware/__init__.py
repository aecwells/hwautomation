"""Hardware management package."""

from .bios import BiosConfigManager
from .discovery import (
    HardwareDiscovery,
    HardwareDiscoveryManager,
    IPMIInfo,
    NetworkInterface,
    SystemInfo,
)
from .ipmi import IpmiManager
from .redfish_manager import RedfishManager

__all__ = [
    "IpmiManager",
    "RedfishManager",
    "BiosConfigManager",
    "HardwareDiscoveryManager",
    "HardwareDiscovery",
    "SystemInfo",
    "IPMIInfo",
    "NetworkInterface",
]
