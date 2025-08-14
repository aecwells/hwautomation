"""
Backward compatibility layer for web core serializers.

This module provides backward compatibility for existing imports while the
codebase migrates to the new modular serializer system.

DEPRECATED: This module is deprecated. Please migrate to:
    from hwautomation.web.serializers import [Serializer Classes]

Migration examples:
    # Old import
    from hwautomation.web.core.serializers import ServerSerializer

    # New import
    from hwautomation.web.serializers import ServerSerializer
"""

import warnings
from typing import Any, Dict, List, Optional

# Import from the new modular location
from hwautomation.web.serializers import (
    APIResponseSerializer,
    BaseSerializer,
    BoardingValidationSerializer,
    DeviceSerializer,
    HardwareSpecSerializer,
    PaginationHelper,
    SerializationCoordinator,
    SerializationMixin,
    SerializerFactory,
    ServerListSerializer,
    ServerSerializer,
    ValidationErrorSerializer,
    ValidationResultSerializer,
    WorkflowListSerializer,
    WorkflowSerializer,
    api_response,
    coordinator,
    paginated_response,
    serialize,
)

# Issue deprecation warning when this module is imported
warnings.warn(
    "hwautomation.web.core.serializers is deprecated. "
    "Please import from hwautomation.web.serializers instead. "
    "This compatibility layer will be removed in a future version.",
    DeprecationWarning,
    stacklevel=2,
)

# Re-export all classes and functions for backward compatibility
__all__ = [
    # Base classes
    "BaseSerializer",
    "SerializationMixin",
    # Entity serializers
    "ServerSerializer",
    "ServerListSerializer",
    "WorkflowSerializer",
    "WorkflowListSerializer",
    "DeviceSerializer",
    "HardwareSpecSerializer",
    "ValidationResultSerializer",
    "BoardingValidationSerializer",
    "ValidationErrorSerializer",
    # Response utilities
    "APIResponseSerializer",
    "PaginationHelper",
    # Coordination
    "SerializerFactory",
    "SerializationCoordinator",
    "coordinator",
    # Convenience functions
    "serialize",
    "api_response",
    "paginated_response",
]
