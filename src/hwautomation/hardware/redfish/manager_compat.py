"""
Redfish Manager Backward Compatibility Layer

This module provides backward compatibility for the original manager.py file.
It re-exports the modular components with the same interface to ensure existing code continues to work.

DEPRECATION NOTICE:
This compatibility layer is provided for transition purposes.
Please update your imports to use the new modular structure:

OLD:
    from hwautomation.hardware.redfish.manager import RedfishManager

NEW:
    from hwautomation.hardware.redfish.managers import RedfishCoordinator as RedfishManager

This file will be removed in a future version.
"""

import warnings
from typing import Any, Dict

# Import all components from the new modular structure
from .managers import (
    BaseRedfishManager,
    RedfishBiosManager,
    RedfishCoordinator,
    RedfishFirmwareManager,
    RedfishManagerConnectionError,
    RedfishManagerError,
    RedfishManagerOperationError,
    RedfishPowerManager,
    RedfishSystemManager,
)

# Issue deprecation warning
warnings.warn(
    "Importing from 'redfish.manager' is deprecated. "
    "Please use 'from hwautomation.hardware.redfish.managers import RedfishCoordinator as RedfishManager' instead. "
    "This compatibility layer will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

# Main backward compatibility alias
RedfishManager = RedfishCoordinator

# Re-export everything for backward compatibility
__all__ = [
    "RedfishManager",  # Main backward compatibility alias
    "RedfishCoordinator",
    "RedfishPowerManager",
    "RedfishBiosManager",
    "RedfishFirmwareManager",
    "RedfishSystemManager",
    "BaseRedfishManager",
    "RedfishManagerError",
    "RedfishManagerConnectionError",
    "RedfishManagerOperationError",
]

# Legacy exception imports for compatibility
try:
    from ..base import RedfishError

    __all__.append("RedfishError")
except ImportError:
    # If base module doesn't exist, define it here
    class RedfishError(Exception):
        """Base Redfish error for backward compatibility."""

        pass


def create_redfish_manager(
    host: str, username: str, password: str, **kwargs
) -> RedfishCoordinator:
    """
    Legacy factory function for creating RedfishManager instances.

    Args:
        host: Redfish service host
        username: Authentication username
        password: Authentication password
        **kwargs: Additional arguments

    Returns:
        RedfishCoordinator instance (aliased as RedfishManager)
    """
    warnings.warn(
        "create_redfish_manager() is deprecated. "
        "Use RedfishCoordinator(host, username, password, ...) directly instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return RedfishCoordinator(host, username, password, **kwargs)


# Legacy compatibility functions
def get_redfish_manager():
    """Legacy function for backward compatibility."""
    warnings.warn(
        "get_redfish_manager() is deprecated. "
        "Create RedfishCoordinator instances directly.",
        DeprecationWarning,
        stacklevel=2,
    )
    return None
