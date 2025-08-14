"""
Redfish Managers Module

Modular Redfish management system with specialized managers.

This module provides a clean separation of concerns for Redfish operations:
- Base manager interface and common utilities
- Power management specialist
- BIOS configuration specialist
- System information and discovery specialist
- Firmware management specialist
- Coordinator that unifies all managers

Usage:
    from hwautomation.hardware.redfish.managers import RedfishCoordinator

    # Create unified manager (backward compatible)
    manager = RedfishCoordinator(
        host="redfish.example.com",
        username="admin",
        password="password"
    )

    # Use specialized managers directly
    from hwautomation.hardware.redfish.managers import (
        RedfishPowerManager,
        RedfishBiosManager,
        RedfishFirmwareManager,
        RedfishSystemManager
    )

    credentials = RedfishCredentials(host="redfish.example.com", ...)
    power_manager = RedfishPowerManager(credentials)
    power_state = power_manager.get_power_state()
"""

# Core managers
from .base import (
    BaseRedfishManager,
    RedfishManagerConnectionError,
    RedfishManagerError,
    RedfishManagerOperationError,
)
from .bios import RedfishBiosManager
from .coordinator import RedfishCoordinator
from .firmware import RedfishFirmwareManager
from .power import RedfishPowerManager
from .system import RedfishSystemManager

# Convenience imports for backward compatibility
__all__ = [
    # Base classes
    "BaseRedfishManager",
    "RedfishManagerError",
    "RedfishManagerConnectionError",
    "RedfishManagerOperationError",
    # Specialized managers
    "RedfishPowerManager",
    "RedfishBiosManager",
    "RedfishFirmwareManager",
    "RedfishSystemManager",
    # Unified coordinator
    "RedfishCoordinator",
]

# Version info
__version__ = "1.0.0"
__author__ = "HWAutomation Team"
__description__ = "Modular Redfish management system with specialized managers"
