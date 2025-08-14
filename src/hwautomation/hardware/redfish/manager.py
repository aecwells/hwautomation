"""
Redfish Management Integration

BACKWARD COMPATIBILITY LAYER - This file has been refactored into a modular structure.

The original manager.py has been split into multiple focused modules:
- managers/base.py: Base manager interface and common utilities
- managers/power.py: Power management specialist
- managers/bios.py: BIOS configuration specialist
- managers/system.py: System information and discovery specialist
- managers/firmware.py: Firmware management specialist
- managers/coordinator.py: Unified coordinator manager

For new code, please use:
    from hwautomation.hardware.redfish.managers import RedfishCoordinator as RedfishManager

This file maintains backward compatibility but will show deprecation warnings.
"""

# Import everything from the compatibility layer
from .manager_compat import *
