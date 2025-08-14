"""
Serializers for HWAutomation Web Interface.

DEPRECATED: This module has been refactored into a modular system.
Please import from hwautomation.web.serializers instead.

This module provides backward compatibility for existing imports while the
codebase migrates to the new modular serializer system.

Migration examples:
    # Old import
    from hwautomation.web.core.serializers import ServerSerializer

    # New import
    from hwautomation.web.serializers import ServerSerializer

The new modular system provides:
- Better separation of concerns
- Individual serializer modules
- Enhanced performance
- Easier testing and maintenance
"""

import warnings

# Issue deprecation warning
warnings.warn(
    "hwautomation.web.core.serializers is deprecated. "
    "Please import from hwautomation.web.serializers instead. "
    "This module will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

# Import from new modular location for backward compatibility
from hwautomation.web.serializers import *  # noqa: F401, F403
