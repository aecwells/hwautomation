"""Hardware management package."""

from .bios import BiosConfigManager
from .discovery import (
    HardwareDiscovery,
    HardwareDiscoveryManager,
    IPMIInfo,
    NetworkInterface,
    SystemInfo,
)
from .firmware import FirmwareManager
from .ipmi import IpmiManager
from .redfish import RedfishManager

__all__ = [
    "IpmiManager",
    "RedfishManager",
    "BiosConfigManager",
    "FirmwareManager",
    "HardwareDiscoveryManager",
    "HardwareDiscovery",
    "SystemInfo",
    "IPMIInfo",
    "NetworkInterface",
]
