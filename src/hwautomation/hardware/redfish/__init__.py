"""Redfish hardware management module.

This package provides a modular implementation of Redfish operations
for server management, replacing the legacy redfish_manager.py with
a clean, extensible architecture.

The package is organized as follows:
- base: Core abstractions, data models, and exceptions
- client: HTTP session management and service discovery
- operations: Specific operation implementations (power, BIOS, firmware, system)
- manager: Unified interface maintaining backward compatibility
"""

from .base import (
    BiosAttribute,
    FirmwareComponent,
    HealthStatus,
    PowerAction,
    PowerState,
    RedfishCapabilities,
    RedfishCredentials,
    RedfishError,
    RedfishOperation,
    RedfishResponse,
    SystemInfo,
)
from .client import RedfishDiscovery, RedfishSession, ServiceRoot
from .manager import RedfishManager
from .operations import (
    RedfishBiosOperation,
    RedfishFirmwareOperation,
    RedfishPowerOperation,
    RedfishSystemOperation,
)

# Legacy compatibility - export main class
RedfishManager = RedfishManager

__all__ = [
    # Main interface
    "RedfishManager",
    
    # Base classes and data models
    "RedfishCredentials",
    "RedfishResponse",
    "RedfishOperation",
    "RedfishError",
    "RedfishCapabilities",
    "SystemInfo",
    "BiosAttribute", 
    "FirmwareComponent",
    "PowerState",
    "PowerAction",
    "HealthStatus",
    
    # Client modules
    "RedfishSession",
    "RedfishDiscovery",
    "ServiceRoot",
    
    # Operation modules
    "RedfishPowerOperation",
    "RedfishSystemOperation",
    "RedfishBiosOperation", 
    "RedfishFirmwareOperation",
]
