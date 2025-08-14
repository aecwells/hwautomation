"""
HWAutomation BIOS Managers.

This module provides a modular BIOS management system with specialized
managers for different vendors and protocols.

Usage:
    from hwautomation.hardware.bios.managers import apply_bios_config, coordinator
    from hwautomation.hardware.bios.managers import RedfishBiosManager, DellBiosManager

    # Convenience function with automatic manager selection
    result = apply_bios_config(
        device_type="a1.c5.large",
        target_ip="192.168.1.100",
        username="ADMIN",
        password="password",
        dry_run=True
    )

    # Direct manager usage
    manager = RedfishBiosManager()
    result = manager.apply_bios_config_smart(...)

    # Coordinator usage
    result = coordinator.apply_bios_config(...)
"""

# Import all managers for easy access
from .base import BaseBiosManagerImpl, BiosManagerInterface, BiosManagerMixin
from .coordinator import (
    BiosManagerCoordinator,
    BiosManagerFactory,
    apply_bios_config,
    coordinator,
    get_device_config,
    select_optimal_method,
)
from .ipmi import IpmiBiosManager
from .redfish import RedfishBiosManager
from .vendor import (
    DellBiosManager,
    HpeBiosManager,
    SupermicroBiosManager,
    VendorBiosManager,
)

# Backward compatibility exports
__all__ = [
    # Base classes
    "BiosManagerInterface",
    "BaseBiosManagerImpl",
    "BiosManagerMixin",
    # Specific managers
    "RedfishBiosManager",
    "DellBiosManager",
    "HpeBiosManager",
    "SupermicroBiosManager",
    "VendorBiosManager",
    "IpmiBiosManager",
    # Coordination
    "BiosManagerFactory",
    "BiosManagerCoordinator",
    "coordinator",
    # Convenience functions
    "apply_bios_config",
    "select_optimal_method",
    "get_device_config",
]
