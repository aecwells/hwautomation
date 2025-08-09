"""IPMI management module.

This module provides a modular IPMI management system that consolidates
basic IPMI operations with vendor-specific configuration capabilities.
"""

from .base import (
    IPMICredentials,
    IPMISettings,
    IPMIConfigResult,
    IPMISystemInfo,
    IPMIVendor,
    PowerState,
    PowerStatus,
    SensorReading,
    IPMICommandError,
    IPMIConnectionError,
    IPMIConfigurationError,
)
from .manager import IpmiManager

__all__ = [
    "IpmiManager",
    "IPMICredentials",
    "IPMISettings", 
    "IPMIConfigResult",
    "IPMISystemInfo",
    "IPMIVendor",
    "PowerState",
    "PowerStatus",
    "SensorReading",
    "IPMICommandError",
    "IPMIConnectionError", 
    "IPMIConfigurationError",
]
