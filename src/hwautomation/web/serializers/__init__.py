"""
HWAutomation Web Serializers.

This module provides a modular serialization system for the HWAutomation
web interface, with specialized serializers for different data types.

Usage:
    from hwautomation.web.serializers import serialize, api_response
    from hwautomation.web.serializers import ServerSerializer, WorkflowSerializer

    # Convenience functions
    data = serialize(server_data, "server")
    response = api_response(data, message="Server retrieved successfully")

    # Direct serializer usage
    serializer = ServerSerializer()
    formatted_data = serializer.serialize(server_data)
"""

# Import all serializers for easy access
from .base import BaseSerializer, SerializationMixin
from .coordinator import (
    SerializationCoordinator,
    SerializerFactory,
    api_response,
    coordinator,
    paginated_response,
    serialize,
)
from .device import DeviceSerializer, HardwareSpecSerializer
from .response import APIResponseSerializer, PaginationHelper
from .server import ServerListSerializer, ServerSerializer
from .validation import (
    BoardingValidationSerializer,
    ValidationErrorSerializer,
    ValidationResultSerializer,
)
from .workflow import WorkflowListSerializer, WorkflowSerializer

# Backward compatibility exports
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
