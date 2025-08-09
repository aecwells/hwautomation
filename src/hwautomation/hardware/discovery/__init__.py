"""Hardware discovery package.

This package provides modular hardware discovery functionality with
support for multiple vendors and extensible parsing capabilities.
"""

from .base import (
    BaseParser,
    BaseVendorDiscovery,
    HardwareDiscovery,
    IPMIInfo,
    NetworkInterface,
    SystemInfo,
)
from .manager import HardwareDiscoveryManager

# Maintain backward compatibility by importing the old class
HardwareDiscoveryManager = HardwareDiscoveryManager

__all__ = [
    "HardwareDiscovery",
    "HardwareDiscoveryManager",
    "IPMIInfo",
    "NetworkInterface",
    "SystemInfo",
    "BaseVendorDiscovery",
    "BaseParser",
]
